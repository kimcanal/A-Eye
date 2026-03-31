using System.IO;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class CapstoneSceneBuilder
{
    private const string ScenePath = "Assets/Scenes/CapstoneModule1.unity";
    private const string ScreenshotPath = "/Users/kenny31/Documents/Capstone/outputs/module1/unity_module1_view.png";
    private const string ScenarioPath = "/Users/kenny31/Documents/Capstone/outputs/module1/unity_scenario.json";
    private static readonly Dictionary<string, Material> MaterialCache = new Dictionary<string, Material>();

    [System.Serializable]
    private class ScenarioData
    {
        public TaxiSlot[] taxis;
        public ObstacleSlot[] obstacles;
    }

    [System.Serializable]
    private class TaxiSlot
    {
        public string name;
        public string zone_id;
        public int dispatch_rank;
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
        ApplyFallbackMaterials(mapInstance);

        var mapBounds = CalculateBounds(mapInstance);
        var center = mapBounds.center;
        var extents = mapBounds.extents;
        var scenario = LoadScenario();

        if (scenario != null && scenario.taxis != null)
        {
            foreach (var taxiSlot in scenario.taxis)
            {
                var taxiName = $"{taxiSlot.name}_{taxiSlot.zone_id}_R{taxiSlot.dispatch_rank}";
                PlacePrefab(
                    taxiPrefab,
                    scene,
                    center + taxiSlot.position.ToVector3(),
                    Quaternion.Euler(0f, taxiSlot.rotation_y, 0f),
                    taxiName
                );
            }
        }
        else
        {
            PlacePrefab(taxiPrefab, scene, center + new Vector3(-8f, 0.15f, -12f), Quaternion.Euler(0f, 0f, 0f), "Taxi_A");
            PlacePrefab(taxiPrefab, scene, center + new Vector3(4f, 0.15f, -12f), Quaternion.Euler(0f, 180f, 0f), "Taxi_B");
            PlacePrefab(taxiPrefab, scene, center + new Vector3(12f, 0.15f, 6f), Quaternion.Euler(0f, -90f, 0f), "Taxi_C");
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
        cam.transform.position = center + new Vector3(0f, Mathf.Max(32f, extents.magnitude * 1.05f), -extents.z * 0.05f);
        cam.transform.rotation = Quaternion.Euler(65f, 0f, 0f);
        cam.nearClipPlane = 0.1f;
        cam.farClipPlane = 1000f;

        Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
        EditorSceneManager.SaveScene(scene, ScenePath);

        Directory.CreateDirectory(Path.GetDirectoryName(ScreenshotPath));
        SaveScreenshot(cam, ScreenshotPath, 1600, 900);

        Debug.Log($"Saved scene: {ScenePath}");
        Debug.Log($"Saved screenshot: {ScreenshotPath}");
        EditorApplication.Exit(0);
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
}
