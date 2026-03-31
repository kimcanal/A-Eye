using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class CapstoneSceneBuilder
{
    private const string ScenePath = "Assets/Scenes/CapstoneModule1.unity";
    private static readonly Dictionary<string, Material> MaterialCache = new Dictionary<string, Material>();

    private static string RepoRoot => GetRequiredPath("CAPSTONE_ROOT");
    private static string ScreenshotPath => Path.Combine(RepoRoot, "outputs", "module1", "unity_module1_view.png");
    private static string FocusScreenshotPath => Path.Combine(RepoRoot, "outputs", "module1", "unity_module1_focus.png");
    private static string OverlayPointsPath => Path.Combine(RepoRoot, "outputs", "module1", "unity_overlay_points.json");
    private static string ScenarioPath => Path.Combine(RepoRoot, "outputs", "module1", "unity_scenario.json");

    [System.Serializable]
    private class ScenarioData
    {
        public TaxiSlot[] taxis;
        public ObstacleSlot[] obstacles;
    }

    [System.Serializable]
    private class OverlayPointCollection
    {
        public OverlayPoint[] points;
    }

    [System.Serializable]
    private class OverlayPoint
    {
        public string zone_id;
        public int dispatch_rank;
        public string hotspot_label;
        public float viewport_x;
        public float viewport_y;
    }

    [System.Serializable]
    private class TaxiSlot
    {
        public string name;
        public string zone_id;
        public int dispatch_rank;
        public string hotspot_label;
        public float dispatch_demand;
        public float predicted_call_count;
        public float observed_call_count;
        public float available_taxis;
        public float imbalance_score;
        public PositionData position;
        public float rotation_y;
    }

    [System.Serializable]
    private class ObstacleSlot
    {
        public string name;
        public string prefab_key;
        public PositionData position;
        public float rotation_y;
    }

    [System.Serializable]
    private class PositionData
    {
        public float x;
        public float y;
        public float z;

        public Vector3 ToVector3()
        {
            return new Vector3(x, y, z);
        }
    }

    [MenuItem("Capstone/Build Module1 Scene")]
    public static void BuildModule1Scene()
    {
        var repoRoot = RepoRoot;
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        var directionalLight = new GameObject("Directional Light");
        var light = directionalLight.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.15f;
        directionalLight.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

        var mapPrefab = LoadPrefab("Assets/Map/street_main_1.prefab");
        var taxiPrefab = LoadPrefab("Assets/object/car_taxi_1.prefab");
        var conePrefab = LoadPrefab("Assets/00_Model/02_Kakao/03_Prefabs/Con_01_01.prefab");
        var coneAltPrefab = LoadPrefab("Assets/00_Model/02_Kakao/03_Prefabs/Con_02_01.prefab");
        var bollardPrefab = LoadPrefab("Assets/00_Model/02_Kakao/03_Prefabs/Steel_Bollard_01.prefab");
        var fencePrefab = LoadPrefab("Assets/00_Model/02_Kakao/03_Prefabs/Roadfence_01_01.prefab");

        var mapInstance = (GameObject)PrefabUtility.InstantiatePrefab(mapPrefab, scene);
        mapInstance.name = "StreetMain";
        var roadAnchors = CollectRoadAnchors(mapInstance);
        ApplyFallbackMaterials(mapInstance);

        var mapBounds = CalculateBounds(mapInstance);
        var center = mapBounds.center;
        var extents = mapBounds.extents;
        var scenario = LoadScenario();
        var placedOverlayPoints = new List<OverlayPoint>();
        var taxiWorldPositions = new List<Vector3>();
        var focusCameraObject = new GameObject("CapstoneFocusCamera");
        var focusCam = focusCameraObject.AddComponent<Camera>();
        focusCam.backgroundColor = new Color(0.78f, 0.86f, 0.95f);
        focusCam.clearFlags = CameraClearFlags.SolidColor;
        focusCam.fieldOfView = 42f;
        focusCam.nearClipPlane = 0.1f;
        focusCam.farClipPlane = 1000f;

        if (scenario != null && scenario.taxis != null)
        {
            foreach (var taxiSlot in scenario.taxis)
            {
                var taxiName = $"{taxiSlot.name}_{taxiSlot.zone_id}_R{taxiSlot.dispatch_rank}";
                var desiredPosition = center + taxiSlot.position.ToVector3();
                var worldPosition = ResolveRoadAlignedPosition(desiredPosition, roadAnchors);
                var taxiInstance = PlacePrefab(
                    taxiPrefab,
                    scene,
                    worldPosition,
                    Quaternion.Euler(0f, taxiSlot.rotation_y, 0f),
                    taxiName
                );
                DecorateTaxiSpot(taxiInstance, worldPosition, taxiSlot);
                taxiWorldPositions.Add(worldPosition);
                placedOverlayPoints.Add(
                    new OverlayPoint
                    {
                        zone_id = taxiSlot.zone_id,
                        dispatch_rank = taxiSlot.dispatch_rank,
                        hotspot_label = taxiSlot.hotspot_label,
                    }
                );
            }

            SetupFocusCamera(center, focusCam, taxiWorldPositions);
        }
        else
        {
            PlacePrefab(taxiPrefab, scene, center + new Vector3(-8f, 0.15f, -12f), Quaternion.Euler(0f, 0f, 0f), "Taxi_A");
            PlacePrefab(taxiPrefab, scene, center + new Vector3(4f, 0.15f, -12f), Quaternion.Euler(0f, 180f, 0f), "Taxi_B");
            PlacePrefab(taxiPrefab, scene, center + new Vector3(12f, 0.15f, 6f), Quaternion.Euler(0f, -90f, 0f), "Taxi_C");
            SetupFocusCamera(
                center,
                focusCam,
                new List<Vector3>
                {
                    center + new Vector3(-8f, 0.15f, -12f),
                    center + new Vector3(4f, 0.15f, -12f),
                    center + new Vector3(12f, 0.15f, 6f),
                }
            );
        }

        if (scenario != null && scenario.obstacles != null)
        {
            foreach (var obstacleSlot in scenario.obstacles)
            {
                var obstaclePrefab = ResolveObstaclePrefab(
                    obstacleSlot.prefab_key,
                    conePrefab,
                    coneAltPrefab,
                    bollardPrefab,
                    fencePrefab
                );

                if (obstaclePrefab == null)
                {
                    continue;
                }

                PlacePrefab(
                    obstaclePrefab,
                    scene,
                    center + obstacleSlot.position.ToVector3(),
                    Quaternion.Euler(0f, obstacleSlot.rotation_y, 0f),
                    obstacleSlot.name
                );
            }
        }
        else
        {
            PlacePrefab(conePrefab, scene, center + new Vector3(-2f, 0.02f, -4f), Quaternion.identity, "Obstacle_Cone_A");
            PlacePrefab(coneAltPrefab, scene, center + new Vector3(-1f, 0.02f, -4.5f), Quaternion.identity, "Obstacle_Cone_B");
            PlacePrefab(bollardPrefab, scene, center + new Vector3(6f, 0.02f, 3f), Quaternion.identity, "Obstacle_Bollard");
            PlacePrefab(fencePrefab, scene, center + new Vector3(10f, 0.02f, -2f), Quaternion.Euler(0f, 90f, 0f), "Obstacle_Fence");
        }

        var cameraObject = new GameObject("CapstoneCamera");
        var cam = cameraObject.AddComponent<Camera>();
        cam.backgroundColor = new Color(0.78f, 0.86f, 0.95f);
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.transform.position = center + new Vector3(0f, Mathf.Max(19f, extents.magnitude * 0.60f), -extents.z * 0.88f);
        cam.transform.rotation = Quaternion.Euler(50f, 0f, 0f);
        cam.nearClipPlane = 0.1f;
        cam.farClipPlane = 1000f;

        Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
        EditorSceneManager.SaveScene(scene, ScenePath);

        Directory.CreateDirectory(Path.GetDirectoryName(ScreenshotPath));
        SaveOverlayPoints(cam, taxiWorldPositions, placedOverlayPoints, OverlayPointsPath);
        SaveScreenshot(cam, ScreenshotPath, 1600, 900);

        focusCam.backgroundColor = cam.backgroundColor;
        focusCam.transform.position = cam.transform.position + new Vector3(0f, -6f, 8f);
        focusCam.transform.rotation = cam.transform.rotation;
        focusCam.fieldOfView = 34f;
        SaveScreenshot(focusCam, FocusScreenshotPath, 1600, 900);

        Debug.Log($"Saved scene: {ScenePath}");
        Debug.Log($"Saved screenshot: {ScreenshotPath}");
        Debug.Log($"Saved focus screenshot: {FocusScreenshotPath}");
        Debug.Log($"Saved overlay points: {OverlayPointsPath}");
        Debug.Log($"Repo root: {repoRoot}");
        EditorApplication.Exit(0);
    }

    private static string GetRequiredPath(string name)
    {
        var value = System.Environment.GetEnvironmentVariable(name);
        if (string.IsNullOrEmpty(value))
        {
            throw new IOException($"Required environment variable is missing: {name}");
        }

        return value;
    }

    private static ScenarioData LoadScenario()
    {
        if (!File.Exists(ScenarioPath))
        {
            Debug.LogWarning($"Scenario file not found: {ScenarioPath}");
            return null;
        }

        var json = File.ReadAllText(ScenarioPath);
        return JsonUtility.FromJson<ScenarioData>(json);
    }

    private static GameObject LoadPrefab(string assetPath)
    {
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
        if (prefab == null)
        {
            throw new FileNotFoundException($"Missing prefab: {assetPath}");
        }

        return prefab;
    }

    private static GameObject PlacePrefab(GameObject prefab, Scene scene, Vector3 position, Quaternion rotation, string name)
    {
        var instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab, scene);
        instance.transform.SetPositionAndRotation(position, rotation);
        instance.name = name;
        ApplyFallbackMaterials(instance);
        return instance;
    }

    private static GameObject ResolveObstaclePrefab(
        string prefabKey,
        GameObject conePrefab,
        GameObject coneAltPrefab,
        GameObject bollardPrefab,
        GameObject fencePrefab
    )
    {
        switch (prefabKey)
        {
            case "cone":
                return conePrefab;
            case "cone_alt":
                return coneAltPrefab;
            case "bollard":
                return bollardPrefab;
            case "fence":
                return fencePrefab;
            default:
                return null;
        }
    }

    private static List<Vector3> CollectRoadAnchors(GameObject root)
    {
        var anchors = new List<Vector3>();
        var rootBounds = CalculateBounds(root);
        var groundThreshold = rootBounds.min.y + 1.2f;

        foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
        {
            if (!IsRoadRenderer(renderer))
            {
                continue;
            }

            var bounds = renderer.bounds;
            if (bounds.max.y > groundThreshold)
            {
                continue;
            }

            if (bounds.size.x < 1f || bounds.size.z < 1f)
            {
                continue;
            }

            anchors.Add(new Vector3(bounds.center.x, bounds.max.y + 0.18f, bounds.center.z));
        }

        return anchors;
    }

    private static bool IsRoadRenderer(Renderer renderer)
    {
        if (renderer.sharedMaterials == null)
        {
            return false;
        }

        foreach (var material in renderer.sharedMaterials)
        {
            if (material == null)
            {
                continue;
            }

            var name = material.name.ToLowerInvariant();
            if (
                name.Contains("road") ||
                name.Contains("asphalt") ||
                name.Contains("cross") ||
                name.Contains("line") ||
                name.Contains("yield") ||
                name.Contains("bicycle")
            )
            {
                return true;
            }
        }

        return false;
    }

    private static Vector3 ResolveRoadAlignedPosition(Vector3 desiredPosition, List<Vector3> roadAnchors)
    {
        if (roadAnchors == null || roadAnchors.Count == 0)
        {
            return desiredPosition;
        }

        var bestIndex = 0;
        var bestDistance = Vector3.Distance(desiredPosition, roadAnchors[0]);
        for (int i = 1; i < roadAnchors.Count; i++)
        {
            var distance = Vector3.Distance(desiredPosition, roadAnchors[i]);
            if (distance < bestDistance)
            {
                bestDistance = distance;
                bestIndex = i;
            }
        }

        var chosen = roadAnchors[bestIndex];
        roadAnchors.RemoveAt(bestIndex);
        return chosen;
    }

    private static void DecorateTaxiSpot(GameObject taxiInstance, Vector3 worldPosition, TaxiSlot taxiSlot)
    {
        var marker = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        marker.name = $"{taxiSlot.name}_Marker";
        marker.transform.position = worldPosition + new Vector3(0f, 0.02f, 0f);
        marker.transform.localScale = new Vector3(2.6f, 0.08f, 2.6f);

        var markerMaterial = new Material(Shader.Find("Standard"));
        markerMaterial.color = GetRankColor(taxiSlot.dispatch_rank);
        markerMaterial.SetFloat("_Glossiness", 0.08f);
        marker.GetComponent<Renderer>().sharedMaterial = markerMaterial;

        var beacon = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        beacon.name = $"{taxiSlot.name}_Beacon";
        beacon.transform.position = worldPosition + new Vector3(0f, 1.25f, 0f);
        beacon.transform.localScale = new Vector3(0.9f, 0.9f, 0.9f);
        beacon.GetComponent<Renderer>().sharedMaterial = markerMaterial;

        var labelPlate = GameObject.CreatePrimitive(PrimitiveType.Cube);
        labelPlate.name = $"{taxiSlot.name}_LabelPlate";
        labelPlate.transform.position = worldPosition + new Vector3(0f, 2.55f, 0f);
        labelPlate.transform.rotation = Quaternion.Euler(50f, 0f, 0f);
        labelPlate.transform.localScale = new Vector3(2.5f, 0.08f, 0.92f);
        var plateMaterial = new Material(Shader.Find("Standard"));
        plateMaterial.color = new Color(0.97f, 0.97f, 0.95f);
        plateMaterial.SetFloat("_Glossiness", 0.02f);
        labelPlate.GetComponent<Renderer>().sharedMaterial = plateMaterial;

        var labelObject = new GameObject($"{taxiSlot.name}_Label");
        labelObject.transform.position = worldPosition + new Vector3(0f, 2.62f, 0f);
        var text = labelObject.AddComponent<TextMesh>();
        text.text = $"R{taxiSlot.dispatch_rank} / {ShortZone(taxiSlot.zone_id)}\n{ShortHotspot(taxiSlot.hotspot_label)}";
        text.characterSize = 0.14f;
        text.fontSize = 30;
        text.anchor = TextAnchor.MiddleCenter;
        text.alignment = TextAlignment.Center;
        text.color = new Color(0.12f, 0.12f, 0.12f);
        labelObject.transform.rotation = Quaternion.Euler(50f, 0f, 0f);

        taxiInstance.transform.localScale = taxiInstance.transform.localScale * 1.55f;
    }

    private static string ShortZone(string zoneId)
    {
        if (string.IsNullOrEmpty(zoneId) || zoneId.Length <= 4)
        {
            return zoneId;
        }

        return zoneId.Substring(zoneId.Length - 4);
    }

    private static string ShortHotspot(string hotspotLabel)
    {
        switch (hotspotLabel)
        {
            case "West Gate":
                return "West";
            case "South Hub":
                return "South";
            case "East Connector":
                return "East";
            default:
                return hotspotLabel;
        }
    }

    private static void SetupFocusCamera(Vector3 center, Camera focusCam, List<Vector3> taxiWorldPositions)
    {
        if (taxiWorldPositions == null || taxiWorldPositions.Count == 0)
        {
            focusCam.transform.position = center + new Vector3(0f, 10.5f, -9.5f);
            focusCam.transform.rotation = Quaternion.Euler(38f, 0f, 0f);
            return;
        }

        var focusCenter = Vector3.zero;
        foreach (var position in taxiWorldPositions)
        {
            focusCenter += position;
        }
        focusCenter /= taxiWorldPositions.Count;

        focusCam.transform.position = focusCenter + new Vector3(0f, 7.5f, -8.5f);
        focusCam.transform.LookAt(focusCenter + new Vector3(0f, 0.6f, 0f));
    }

    private static Color GetRankColor(int dispatchRank)
    {
        switch (dispatchRank)
        {
            case 1:
                return new Color(0.97f, 0.55f, 0.15f);
            case 2:
                return new Color(0.96f, 0.73f, 0.18f);
            case 3:
                return new Color(0.98f, 0.84f, 0.32f);
            default:
                return new Color(0.85f, 0.85f, 0.85f);
        }
    }

    private static void ApplyFallbackMaterials(GameObject root)
    {
        foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
        {
            var sharedMaterials = renderer.sharedMaterials;
            for (int i = 0; i < sharedMaterials.Length; i++)
            {
                var original = sharedMaterials[i];
                if (original == null)
                {
                    continue;
                }

                sharedMaterials[i] = GetOrCreateFallbackMaterial(original);
            }

            renderer.sharedMaterials = sharedMaterials;
        }
    }

    private static Material GetOrCreateFallbackMaterial(Material original)
    {
        var key = original.name;
        if (MaterialCache.TryGetValue(key, out var cached))
        {
            return cached;
        }

        var shader = Shader.Find("Standard");
        var fallback = new Material(shader);
        fallback.name = $"Fallback_{original.name}";
        fallback.color = InferColor(original.name);
        fallback.SetFloat("_Glossiness", InferGlossiness(original.name));

        var texture = original.mainTexture;
        if (texture != null)
        {
            fallback.mainTexture = texture;
            fallback.color = Color.white;
        }

        MaterialCache[key] = fallback;
        return fallback;
    }

    private static Color InferColor(string materialName)
    {
        var name = materialName.ToLowerInvariant();

        if (name.Contains("taxi") || name.Contains("yellow"))
        {
            return new Color(0.96f, 0.77f, 0.13f);
        }

        if (name.Contains("window") || name.Contains("glass"))
        {
            return new Color(0.70f, 0.82f, 0.90f);
        }

        if (name.Contains("tire") || name.Contains("rubber") || name.Contains("black"))
        {
            return new Color(0.13f, 0.13f, 0.13f);
        }

        if (name.Contains("road") || name.Contains("asphalt") || name.Contains("line") || name.Contains("cross"))
        {
            return new Color(0.23f, 0.24f, 0.27f);
        }

        if (name.Contains("grass") || name.Contains("tree") || name.Contains("leaf"))
        {
            return new Color(0.34f, 0.55f, 0.28f);
        }

        if (name.Contains("concrete") || name.Contains("tile") || name.Contains("wall") || name.Contains("white"))
        {
            return new Color(0.83f, 0.83f, 0.80f);
        }

        if (name.Contains("metal") || name.Contains("steel") || name.Contains("bollard"))
        {
            return new Color(0.58f, 0.60f, 0.62f);
        }

        if (name.Contains("orange") || name.Contains("cone"))
        {
            return new Color(0.98f, 0.46f, 0.12f);
        }

        return new Color(0.75f, 0.75f, 0.75f);
    }

    private static float InferGlossiness(string materialName)
    {
        var name = materialName.ToLowerInvariant();
        if (name.Contains("road") || name.Contains("asphalt") || name.Contains("concrete"))
        {
            return 0.05f;
        }

        if (name.Contains("glass") || name.Contains("metal"))
        {
            return 0.35f;
        }

        return 0.15f;
    }

    private static Bounds CalculateBounds(GameObject root)
    {
        var renderers = root.GetComponentsInChildren<Renderer>();
        if (renderers.Length == 0)
        {
            return new Bounds(root.transform.position, new Vector3(50f, 1f, 50f));
        }

        var bounds = renderers[0].bounds;
        for (int i = 1; i < renderers.Length; i++)
        {
            bounds.Encapsulate(renderers[i].bounds);
        }
        return bounds;
    }

    private static void SaveScreenshot(Camera cam, string outputPath, int width, int height)
    {
        var rt = new RenderTexture(width, height, 24);
        var previous = cam.targetTexture;
        var previousActive = RenderTexture.active;
        cam.targetTexture = rt;
        RenderTexture.active = rt;
        cam.Render();

        var image = new Texture2D(width, height, TextureFormat.RGB24, false);
        image.ReadPixels(new Rect(0, 0, width, height), 0, 0);
        image.Apply();

        var bytes = image.EncodeToPNG();
        File.WriteAllBytes(outputPath, bytes);

        cam.targetTexture = previous;
        RenderTexture.active = previousActive;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(image);
    }

    private static void SaveOverlayPoints(
        Camera cam,
        List<Vector3> taxiWorldPositions,
        List<OverlayPoint> points,
        string outputPath
    )
    {
        if (points == null || taxiWorldPositions == null || points.Count != taxiWorldPositions.Count)
        {
            return;
        }

        for (int i = 0; i < points.Count; i++)
        {
            var viewport = cam.WorldToViewportPoint(taxiWorldPositions[i] + new Vector3(0f, 1.2f, 0f));
            points[i].viewport_x = viewport.x;
            points[i].viewport_y = viewport.y;
        }

        var payload = new OverlayPointCollection
        {
            points = points.ToArray(),
        };

        File.WriteAllText(outputPath, JsonUtility.ToJson(payload, true));
    }
}
