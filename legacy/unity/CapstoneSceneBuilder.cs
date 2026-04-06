using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class CapstoneSceneBuilder
{
    private const string LegacyScenePath = "Assets/Scenes/CapstoneModule1.unity";
    private const string OverviewScenePath = "Assets/Scenes/CapstoneModule1_Overview.unity";
    private const string MotionDemoScenePath = "Assets/Scenes/CapstoneModule1_MotionDemo.unity";
    private const string DefaultRepoRoot = "/Users/kenny31/Documents/Capstone";
    private const string AutoCleanSessionKey = "Capstone.AutoCleanMissingScriptsDone";
    private static readonly Dictionary<string, Material> MaterialCache = new Dictionary<string, Material>();

    private static string RepoRoot => ResolveRepoRoot();
    private static string Module1OutputDir => Path.Combine(RepoRoot, "outputs", "module1");
    private static string ScratchOutputDir => Path.Combine(Module1OutputDir, "scratch");
    private static string OverviewScreenshotPath => Path.Combine(ScratchOutputDir, "unity_module1_view.png");
    private static string OverviewFocusScreenshotPath => Path.Combine(ScratchOutputDir, "unity_module1_focus.png");
    private static string OverviewOverlayPointsPath => Path.Combine(ScratchOutputDir, "unity_overlay_points.json");
    private static string MotionDemoScreenshotPath => Path.Combine(ScratchOutputDir, "unity_module1_motion_view.png");
    private static string MotionDemoFocusScreenshotPath => Path.Combine(ScratchOutputDir, "unity_module1_motion_focus.png");
    private static string MotionDemoOverlayPointsPath => Path.Combine(ScratchOutputDir, "unity_overlay_points_motion.json");
    private static string ScenarioPath => Path.Combine(Module1OutputDir, "unity_scenario.json");
    private static string RepoRootConfigPath => Path.Combine(Application.dataPath, "Editor", "CapstoneRepoRoot.txt");

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

    [InitializeOnLoadMethod]
    private static void AutoCleanMissingScriptsOnEditorLoad()
    {
        if (Application.isBatchMode || SessionState.GetBool(AutoCleanSessionKey, false))
        {
            return;
        }

        SessionState.SetBool(AutoCleanSessionKey, true);
        EditorApplication.delayCall += () =>
        {
            try
            {
                CleanMissingScriptsInMapPrefab();
                CleanMissingScriptsInActiveScene();
            }
            catch (System.Exception ex)
            {
                Debug.LogWarning($"Capstone auto-clean skipped: {ex.Message}");
            }
        };
    }

    [MenuItem("Capstone/Build Module1 Scene")]
    public static void BuildModule1Scene()
    {
        BuildOverviewScene();
    }

    [MenuItem("Capstone/Restore Digital Twin Overview")]
    public static void RestoreDigitalTwinOverview()
    {
        BuildOverviewScene();
    }

    [MenuItem("Capstone/Build Module1 Overview Scene")]
    public static void BuildOverviewScene()
    {
        BuildScene(isMotionDemo: false);
    }

    [MenuItem("Capstone/Build Module1 Motion Demo Scene")]
    public static void BuildMotionDemoScene()
    {
        BuildScene(isMotionDemo: true);
    }

    private static void BuildScene(bool isMotionDemo)
    {
        var repoRoot = RepoRoot;
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        var directionalLight = new GameObject("Directional Light");
        var light = directionalLight.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.15f;
        directionalLight.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

        var mapPrefab = TryLoadPrefab("Assets/Map/street_main_1.prefab");
        var taxiPrefab = TryLoadPrefab("Assets/object/car_taxi_1.prefab");
        var conePrefab = TryLoadPrefab("Assets/00_Model/02_Kakao/03_Prefabs/Con_01_01.prefab");
        var coneAltPrefab = TryLoadPrefab("Assets/00_Model/02_Kakao/03_Prefabs/Con_02_01.prefab");
        var bollardPrefab = TryLoadPrefab("Assets/00_Model/02_Kakao/03_Prefabs/Steel_Bollard_01.prefab");
        var fencePrefab = TryLoadPrefab("Assets/00_Model/02_Kakao/03_Prefabs/Roadfence_01_01.prefab");

        GameObject mapInstance;
        if (mapPrefab != null)
        {
            mapInstance = (GameObject)PrefabUtility.InstantiatePrefab(mapPrefab, scene);
            mapInstance.name = "StreetMain";
            RemoveMissingScriptsRecursive(mapInstance, "map");
            ApplyFallbackMaterials(mapInstance);
        }
        else
        {
            Debug.LogWarning("Map prefab not found. Building fallback digital twin city instead.");
            mapInstance = CreateFallbackCity(scene);
        }

        var roadAnchors = CollectRoadAnchors(mapInstance);

        var mapBounds = CalculateBounds(mapInstance);
        var center = mapBounds.center;
        var extents = mapBounds.extents;
        var scenario = LoadScenario();
        var placedOverlayPoints = new List<OverlayPoint>();
        var taxiWorldPositions = new List<Vector3>();
        var taxiInstances = new List<GameObject>();
        var focusCameraObject = new GameObject("CapstoneFocusCamera");
        focusCameraObject.tag = "Untagged";
        var focusCam = focusCameraObject.AddComponent<Camera>();
        focusCam.backgroundColor = new Color(0.78f, 0.86f, 0.95f);
        focusCam.clearFlags = CameraClearFlags.SolidColor;
        focusCam.fieldOfView = 42f;
        focusCam.nearClipPlane = 0.1f;
        focusCam.farClipPlane = 1000f;

        if (scenario != null && scenario.taxis != null)
        {
            var demoPositions = SelectDemoTaxiPositions(roadAnchors, center, scenario.taxis.Length);

            for (int i = 0; i < scenario.taxis.Length; i++)
            {
                var taxiSlot = scenario.taxis[i];
                var taxiName = $"{taxiSlot.name}_{taxiSlot.zone_id}_R{taxiSlot.dispatch_rank}";
                var desiredPosition = center + taxiSlot.position.ToVector3();
                var worldPosition = isMotionDemo
                    ? (i < demoPositions.Count ? demoPositions[i] : ResolveRoadAlignedPosition(desiredPosition, roadAnchors))
                    : ResolveRoadAlignedPosition(desiredPosition, roadAnchors);
                var taxiInstance = PlaceTaxi(
                    taxiPrefab,
                    scene,
                    worldPosition,
                    Quaternion.Euler(0f, taxiSlot.rotation_y, 0f),
                    taxiName
                );
                DecorateTaxiSpot(taxiInstance, worldPosition, taxiSlot);
                taxiWorldPositions.Add(worldPosition);
                taxiInstances.Add(taxiInstance);
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
            Debug.LogWarning($"Scenario missing or empty, using fallback taxi demo from: {ScenarioPath}");

            var fallbackTaxiA = center + new Vector3(-8f, 0.15f, -12f);
            var fallbackTaxiB = center + new Vector3(4f, 0.15f, -12f);
            var fallbackTaxiC = center + new Vector3(12f, 0.15f, 6f);

            taxiInstances.Add(PlaceTaxi(taxiPrefab, scene, fallbackTaxiA, Quaternion.Euler(0f, 0f, 0f), "Taxi_A"));
            taxiInstances.Add(PlaceTaxi(taxiPrefab, scene, fallbackTaxiB, Quaternion.Euler(0f, 180f, 0f), "Taxi_B"));
            taxiInstances.Add(PlaceTaxi(taxiPrefab, scene, fallbackTaxiC, Quaternion.Euler(0f, -90f, 0f), "Taxi_C"));
            taxiWorldPositions.Add(fallbackTaxiA);
            taxiWorldPositions.Add(fallbackTaxiB);
            taxiWorldPositions.Add(fallbackTaxiC);

            SetupFocusCamera(
                center,
                focusCam,
                new List<Vector3>
                {
                    fallbackTaxiA,
                    fallbackTaxiB,
                    fallbackTaxiC,
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

                if (!IsKnownObstacleKey(obstacleSlot.prefab_key))
                {
                    continue;
                }

                PlaceObstacle(
                    obstaclePrefab,
                    obstacleSlot.prefab_key,
                    scene,
                    center + obstacleSlot.position.ToVector3(),
                    Quaternion.Euler(0f, obstacleSlot.rotation_y, 0f),
                    obstacleSlot.name
                );
            }
        }
        else
        {
            PlaceObstacle(conePrefab, "cone", scene, center + new Vector3(-2f, 0.02f, -4f), Quaternion.identity, "Obstacle_Cone_A");
            PlaceObstacle(coneAltPrefab, "cone_alt", scene, center + new Vector3(-1f, 0.02f, -4.5f), Quaternion.identity, "Obstacle_Cone_B");
            PlaceObstacle(bollardPrefab, "bollard", scene, center + new Vector3(6f, 0.02f, 3f), Quaternion.identity, "Obstacle_Bollard");
            PlaceObstacle(fencePrefab, "fence", scene, center + new Vector3(10f, 0.02f, -2f), Quaternion.Euler(0f, 90f, 0f), "Obstacle_Fence");
        }

        var cameraObject = new GameObject("CapstoneCamera");
        cameraObject.tag = "MainCamera";
        var cam = cameraObject.AddComponent<Camera>();
        cam.backgroundColor = new Color(0.78f, 0.86f, 0.95f);
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.nearClipPlane = 0.1f;
        cam.farClipPlane = 1000f;

        if (isMotionDemo)
        {
            AttachTaxiRuntime(taxiInstances, scenario);
            ConfigureMotionDemoCamera(cam, taxiInstances, center);
            focusCam.enabled = false;
        }
        else
        {
            ConfigureOverviewCamera(cam, center, extents);
            focusCam.enabled = false;
        }

        var targetScenePath = isMotionDemo ? MotionDemoScenePath : OverviewScenePath;
        var targetScreenshotPath = isMotionDemo ? MotionDemoScreenshotPath : OverviewScreenshotPath;
        var targetFocusScreenshotPath = isMotionDemo ? MotionDemoFocusScreenshotPath : OverviewFocusScreenshotPath;
        var targetOverlayPointsPath = isMotionDemo ? MotionDemoOverlayPointsPath : OverviewOverlayPointsPath;

        Directory.CreateDirectory(Path.GetDirectoryName(targetScenePath));
        EditorSceneManager.SaveScene(scene, targetScenePath);
        if (!isMotionDemo)
        {
            EditorSceneManager.SaveScene(scene, LegacyScenePath);
        }

        Directory.CreateDirectory(Path.GetDirectoryName(targetScreenshotPath));
        SaveOverlayPoints(cam, taxiWorldPositions, placedOverlayPoints, targetOverlayPointsPath);
        SaveScreenshot(cam, targetScreenshotPath, 1600, 900);

        focusCam.backgroundColor = cam.backgroundColor;
        focusCam.transform.position = cam.transform.position + new Vector3(0f, -6f, 8f);
        focusCam.transform.rotation = cam.transform.rotation;
        focusCam.fieldOfView = 34f;
        SaveScreenshot(focusCam, targetFocusScreenshotPath, 1600, 900);

        Debug.Log($"Saved scene: {targetScenePath}");
        if (!isMotionDemo)
        {
            Debug.Log($"Updated legacy scene: {LegacyScenePath}");
        }
        Debug.Log($"Saved screenshot: {targetScreenshotPath}");
        Debug.Log($"Saved focus screenshot: {targetFocusScreenshotPath}");
        Debug.Log($"Saved overlay points: {targetOverlayPointsPath}");
        Debug.Log($"Repo root: {repoRoot}");

        if (Application.isBatchMode)
        {
            EditorApplication.Exit(0);
            return;
        }

        Debug.Log($"Module1 {(isMotionDemo ? "motion demo" : "overview")} scene build finished. Unity stays open for manual testing.");
    }

    [MenuItem("Capstone/Clean Missing Scripts In street_main_1 Prefab")]
    public static void CleanMissingScriptsInMapPrefab()
    {
        const string prefabPath = "Assets/Map/street_main_1.prefab";
        if (TryLoadPrefab(prefabPath) == null)
        {
            Debug.LogWarning($"Map prefab does not exist in this Unity project: {prefabPath}");
            return;
        }

        var prefabRoot = PrefabUtility.LoadPrefabContents(prefabPath);
        try
        {
            var removedCount = RemoveMissingScriptsRecursive(prefabRoot, "street_main_1 prefab");
            PrefabUtility.SaveAsPrefabAsset(prefabRoot, prefabPath);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log($"Cleaned missing scripts from {prefabPath}. Removed {removedCount} component(s).");
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(prefabRoot);
        }
    }

    [MenuItem("Capstone/Clean Missing Scripts In Active Scene")]
    public static void CleanMissingScriptsInActiveScene()
    {
        var scene = SceneManager.GetActiveScene();
        if (!scene.IsValid() || !scene.isLoaded)
        {
            Debug.LogWarning("No active loaded scene is available.");
            return;
        }

        var removedCount = 0;
        foreach (var root in scene.GetRootGameObjects())
        {
            removedCount += RemoveMissingScriptsRecursive(root, $"scene root {root.name}");
        }

        if (removedCount > 0)
        {
            EditorSceneManager.MarkSceneDirty(scene);
        }

        Debug.Log($"Cleaned missing scripts from active scene '{scene.name}'. Removed {removedCount} component(s).");
    }

    private static string ResolveRepoRoot()
    {
        var value = System.Environment.GetEnvironmentVariable("CAPSTONE_ROOT");
        if (!string.IsNullOrEmpty(value) && Directory.Exists(value))
        {
            return value;
        }

        if (File.Exists(RepoRootConfigPath))
        {
            var configured = File.ReadAllText(RepoRootConfigPath).Trim();
            if (!string.IsNullOrEmpty(configured) && Directory.Exists(configured))
            {
                return configured;
            }

            Debug.LogWarning($"Capstone repo root config exists but is invalid: {RepoRootConfigPath}");
        }

        if (Directory.Exists(DefaultRepoRoot))
        {
            return DefaultRepoRoot;
        }

        throw new IOException(
            "CAPSTONE_ROOT is missing and no valid fallback repo path was found. " +
            $"Set CAPSTONE_ROOT or create {RepoRootConfigPath} with the Capstone repo path."
        );
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

    private static GameObject TryLoadPrefab(string assetPath)
    {
        return AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
    }

    private static GameObject PlacePrefab(GameObject prefab, Scene scene, Vector3 position, Quaternion rotation, string name)
    {
        var instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab, scene);
        instance.transform.SetPositionAndRotation(position, rotation);
        instance.name = name;
        RemoveMissingScriptsRecursive(instance, name);
        ApplyFallbackMaterials(instance);
        return instance;
    }

    private static GameObject PlaceTaxi(GameObject taxiPrefab, Scene scene, Vector3 position, Quaternion rotation, string name)
    {
        if (taxiPrefab != null)
        {
            return PlacePrefab(taxiPrefab, scene, position, rotation, name);
        }

        return CreateFallbackTaxi(scene, position, rotation, name);
    }

    private static GameObject PlaceObstacle(
        GameObject obstaclePrefab,
        string prefabKey,
        Scene scene,
        Vector3 position,
        Quaternion rotation,
        string name
    )
    {
        if (obstaclePrefab != null)
        {
            return PlacePrefab(obstaclePrefab, scene, position, rotation, name);
        }

        return CreateFallbackObstacle(scene, prefabKey, position, rotation, name);
    }

    private static GameObject CreateFallbackCity(Scene scene)
    {
        var root = new GameObject("FallbackCity");
        SceneManager.MoveGameObjectToScene(root, scene);

        var ground = CreatePrimitiveChild(root.transform, PrimitiveType.Plane, "Fallback_Ground");
        ground.transform.localScale = new Vector3(6.2f, 1f, 6.2f);
        ground.transform.position = new Vector3(0f, -0.04f, 0f);
        SetMaterial(ground, "Fallback_Concrete", new Color(0.84f, 0.85f, 0.82f), 0.04f);

        var roadOffsets = new[]
        {
            new Vector3(0f, 0.02f, 0f),
            new Vector3(-18f, 0.02f, 0f),
            new Vector3(18f, 0.02f, 0f),
            new Vector3(0f, 0.02f, -18f),
            new Vector3(0f, 0.02f, 18f),
        };

        foreach (var offset in roadOffsets)
        {
            var eastWestRoad = CreatePrimitiveChild(root.transform, PrimitiveType.Cube, $"Fallback_Road_EW_{offset.x}_{offset.z}");
            eastWestRoad.transform.position = offset;
            eastWestRoad.transform.localScale = new Vector3(20f, 0.08f, 8f);
            SetMaterial(eastWestRoad, "Fallback_Asphalt_Road", new Color(0.22f, 0.23f, 0.26f), 0.03f);

            var northSouthRoad = CreatePrimitiveChild(root.transform, PrimitiveType.Cube, $"Fallback_Road_NS_{offset.x}_{offset.z}");
            northSouthRoad.transform.position = offset;
            northSouthRoad.transform.localScale = new Vector3(8f, 0.08f, 20f);
            SetMaterial(northSouthRoad, "Fallback_Asphalt_Road", new Color(0.22f, 0.23f, 0.26f), 0.03f);
        }

        for (int i = -2; i <= 2; i++)
        {
            var laneMarkingHorizontal = CreatePrimitiveChild(root.transform, PrimitiveType.Cube, $"Fallback_LaneMarking_H_{i}");
            laneMarkingHorizontal.transform.position = new Vector3(i * 8f, 0.08f, 0f);
            laneMarkingHorizontal.transform.localScale = new Vector3(3.5f, 0.02f, 0.22f);
            SetMaterial(laneMarkingHorizontal, "Fallback_Road_Line", new Color(0.95f, 0.93f, 0.78f), 0.02f);

            var laneMarkingVertical = CreatePrimitiveChild(root.transform, PrimitiveType.Cube, $"Fallback_LaneMarking_V_{i}");
            laneMarkingVertical.transform.position = new Vector3(0f, 0.08f, i * 8f);
            laneMarkingVertical.transform.localScale = new Vector3(0.22f, 0.02f, 3.5f);
            SetMaterial(laneMarkingVertical, "Fallback_Road_Line", new Color(0.95f, 0.93f, 0.78f), 0.02f);
        }

        var buildingSpecs = new[]
        {
            new Vector3(-22f, 3f, -22f),
            new Vector3(22f, 4f, -22f),
            new Vector3(-22f, 5f, 22f),
            new Vector3(22f, 3.5f, 22f),
            new Vector3(-30f, 2.8f, 6f),
            new Vector3(30f, 4.2f, -6f),
        };

        for (int i = 0; i < buildingSpecs.Length; i++)
        {
            var spec = buildingSpecs[i];
            var building = CreatePrimitiveChild(root.transform, PrimitiveType.Cube, $"Fallback_Building_{i + 1}");
            building.transform.position = spec;
            building.transform.localScale = new Vector3(10f, spec.y * 2f, 10f);
            SetMaterial(building, "Fallback_Building", new Color(0.77f, 0.79f, 0.81f), 0.07f);
        }

        return root;
    }

    private static GameObject CreateFallbackTaxi(Scene scene, Vector3 position, Quaternion rotation, string name)
    {
        var root = new GameObject(name);
        SceneManager.MoveGameObjectToScene(root, scene);
        root.transform.SetPositionAndRotation(position, rotation);

        var body = CreatePrimitiveChild(root.transform, PrimitiveType.Cube, "Body");
        body.transform.localPosition = new Vector3(0f, 0.6f, 0f);
        body.transform.localScale = new Vector3(2.4f, 0.9f, 4.4f);
        SetMaterial(body, "Fallback_Taxi_Yellow", new Color(0.95f, 0.76f, 0.13f), 0.1f);

        var roof = CreatePrimitiveChild(root.transform, PrimitiveType.Cube, "Roof");
        roof.transform.localPosition = new Vector3(0f, 1.15f, -0.1f);
        roof.transform.localScale = new Vector3(1.8f, 0.7f, 2.2f);
        SetMaterial(roof, "Fallback_Taxi_Yellow", new Color(0.95f, 0.76f, 0.13f), 0.1f);

        var cabin = CreatePrimitiveChild(root.transform, PrimitiveType.Cube, "Cabin");
        cabin.transform.localPosition = new Vector3(0f, 1.18f, -0.1f);
        cabin.transform.localScale = new Vector3(1.5f, 0.5f, 1.9f);
        SetMaterial(cabin, "Fallback_Taxi_Glass", new Color(0.68f, 0.82f, 0.92f), 0.25f);

        var wheelOffsets = new[]
        {
            new Vector3(-1f, 0.25f, 1.45f),
            new Vector3(1f, 0.25f, 1.45f),
            new Vector3(-1f, 0.25f, -1.45f),
            new Vector3(1f, 0.25f, -1.45f),
        };

        for (int i = 0; i < wheelOffsets.Length; i++)
        {
            var wheel = CreatePrimitiveChild(root.transform, PrimitiveType.Cylinder, $"Wheel_{i + 1}");
            wheel.transform.localPosition = wheelOffsets[i];
            wheel.transform.localRotation = Quaternion.Euler(0f, 0f, 90f);
            wheel.transform.localScale = new Vector3(0.45f, 0.18f, 0.45f);
            SetMaterial(wheel, "Fallback_Taxi_Wheel", new Color(0.12f, 0.12f, 0.12f), 0.02f);
        }

        return root;
    }

    private static GameObject CreateFallbackObstacle(Scene scene, string prefabKey, Vector3 position, Quaternion rotation, string name)
    {
        var primitiveType = PrimitiveType.Cube;
        var localScale = new Vector3(0.7f, 0.7f, 0.7f);
        var color = new Color(0.98f, 0.46f, 0.12f);
        var glossiness = 0.08f;

        switch (prefabKey)
        {
            case "cone":
                primitiveType = PrimitiveType.Cylinder;
                localScale = new Vector3(0.34f, 0.42f, 0.34f);
                color = new Color(0.98f, 0.46f, 0.12f);
                break;
            case "cone_alt":
                primitiveType = PrimitiveType.Cylinder;
                localScale = new Vector3(0.26f, 0.36f, 0.26f);
                color = new Color(0.99f, 0.60f, 0.18f);
                break;
            case "bollard":
                primitiveType = PrimitiveType.Cylinder;
                localScale = new Vector3(0.22f, 0.7f, 0.22f);
                color = new Color(0.58f, 0.60f, 0.62f);
                glossiness = 0.18f;
                break;
            case "fence":
                primitiveType = PrimitiveType.Cube;
                localScale = new Vector3(4.5f, 0.9f, 0.18f);
                color = new Color(0.74f, 0.76f, 0.78f);
                glossiness = 0.12f;
                break;
        }

        var obstacle = GameObject.CreatePrimitive(primitiveType);
        SceneManager.MoveGameObjectToScene(obstacle, scene);
        obstacle.name = name;
        obstacle.transform.SetPositionAndRotation(position, rotation);
        obstacle.transform.localScale = localScale;
        SetMaterial(obstacle, $"Fallback_{prefabKey}", color, glossiness);
        return obstacle;
    }

    private static GameObject CreatePrimitiveChild(Transform parent, PrimitiveType primitiveType, string name)
    {
        var child = GameObject.CreatePrimitive(primitiveType);
        child.name = name;
        child.transform.SetParent(parent, false);
        return child;
    }

    private static void SetMaterial(GameObject target, string materialName, Color color, float glossiness)
    {
        if (target == null)
        {
            return;
        }

        var renderer = target.GetComponent<Renderer>();
        if (renderer == null)
        {
            return;
        }

        if (!MaterialCache.TryGetValue(materialName, out var material))
        {
            material = new Material(Shader.Find("Standard"));
            material.name = materialName;
            material.color = color;
            material.SetFloat("_Glossiness", glossiness);
            MaterialCache[materialName] = material;
        }

        renderer.sharedMaterial = material;
    }

    private static int RemoveMissingScriptsRecursive(GameObject root, string context)
    {
        if (root == null)
        {
            return 0;
        }

        var removedCount = 0;
        foreach (var transform in root.GetComponentsInChildren<Transform>(true))
        {
            removedCount += GameObjectUtility.RemoveMonoBehavioursWithMissingScript(transform.gameObject);
        }

        if (removedCount > 0)
        {
            Debug.Log($"Removed {removedCount} missing script reference(s) from {context}: {root.name}");
        }

        return removedCount;
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

    private static bool IsKnownObstacleKey(string prefabKey)
    {
        switch (prefabKey)
        {
            case "cone":
            case "cone_alt":
            case "bollard":
            case "fence":
                return true;
            default:
                return false;
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

    private static List<Vector3> SelectDemoTaxiPositions(List<Vector3> roadAnchors, Vector3 center, int count)
    {
        var result = new List<Vector3>();
        if (count <= 0)
        {
            return result;
        }

        var groundY = center.y + 0.32f;
        if (roadAnchors != null && roadAnchors.Count > 0)
        {
            groundY = ResolveRoadAlignedPosition(center, new List<Vector3>(roadAnchors)).y;
        }

        var offsets = new[]
        {
            new Vector3(0f, 0f, 0f),
            new Vector3(-10f, 0f, -10f),
            new Vector3(10f, 0f, 10f),
            new Vector3(-14f, 0f, 8f),
            new Vector3(14f, 0f, -8f),
        };

        for (int i = 0; i < count && i < offsets.Length; i++)
        {
            var offset = offsets[i];
            result.Add(new Vector3(center.x + offset.x, groundY, center.z + offset.z));
        }

        return result;
    }

    private static void DecorateTaxiSpot(GameObject taxiInstance, Vector3 worldPosition, TaxiSlot taxiSlot)
    {
        if (taxiInstance == null)
        {
            return;
        }

        var existingMarker = taxiInstance.transform.Find($"{taxiSlot.name}_Marker");
        if (existingMarker != null)
        {
            Object.DestroyImmediate(existingMarker.gameObject);
        }

        var marker = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        marker.name = $"{taxiSlot.name}_Marker";
        marker.transform.position = worldPosition + new Vector3(0f, 0.02f, 0f);
        marker.transform.localScale = new Vector3(2.6f, 0.08f, 2.6f);
        marker.transform.SetParent(taxiInstance.transform.parent, true);

        var markerMaterial = new Material(Shader.Find("Standard"));
        markerMaterial.color = GetRankColor(taxiSlot.dispatch_rank);
        markerMaterial.SetFloat("_Glossiness", 0.08f);
        marker.GetComponent<Renderer>().sharedMaterial = markerMaterial;
    }

    private static void AttachTaxiRuntime(List<GameObject> taxiInstances, ScenarioData scenario)
    {
        if (taxiInstances == null || taxiInstances.Count == 0)
        {
            Debug.LogWarning("No taxi instances were found for runtime auto-drive.");
            return;
        }

        for (int i = 0; i < taxiInstances.Count; i++)
        {
            var taxiInstance = taxiInstances[i];
            var drive = taxiInstance.GetComponent<CapstoneTaxiAutoDrive>();
            if (drive == null)
            {
                drive = taxiInstance.AddComponent<CapstoneTaxiAutoDrive>();
            }

            var rank = 1;
            if (scenario != null && scenario.taxis != null && i < scenario.taxis.Length)
            {
                rank = Mathf.Max(1, scenario.taxis[i].dispatch_rank);
            }

            var speed = 3.5f + (4 - Mathf.Min(rank, 3)) * 0.65f;
            var route = BuildTaxiRoute(taxiInstance.transform);
            var attachFollowCamera = i == 0;
            drive.Configure(route, speed, attachFollowCamera, enableMotionBeacon: false);
            Debug.Log($"Configured auto-drive for {taxiInstance.name} with {route.Length} waypoint(s) at speed {speed:0.00}");
        }
    }

    private static Vector3[] BuildTaxiRoute(Transform taxiTransform)
    {
        var origin = taxiTransform.position;
        var forward = taxiTransform.forward.normalized;
        var right = taxiTransform.right.normalized;

        return new[]
        {
            origin,
            origin + forward * 24f,
            origin + forward * 24f + right * 12f,
            origin + right * 12f,
        };
    }

    private static void ConfigureMotionDemoCamera(Camera cam, List<GameObject> taxiInstances, Vector3 center)
    {
        if (cam == null)
        {
            return;
        }
        if (taxiInstances == null || taxiInstances.Count == 0)
        {
            ConfigureOverviewCamera(cam, center, Vector3.one * 20f);
            return;
        }

        var focusCenter = Vector3.zero;
        foreach (var taxi in taxiInstances)
        {
            focusCenter += taxi.transform.position;
        }
        focusCenter /= taxiInstances.Count;

        cam.transform.position = focusCenter + new Vector3(0f, 32f, -18f);
        cam.transform.rotation = Quaternion.Euler(60f, 0f, 0f);
        cam.fieldOfView = 38f;
    }

    private static void ConfigureOverviewCamera(Camera cam, Vector3 center, Vector3 extents)
    {
        if (cam == null)
        {
            return;
        }

        var height = Mathf.Max(52f, extents.magnitude * 0.82f);
        cam.transform.position = center + new Vector3(0f, height, -extents.z * 1.05f);
        cam.transform.rotation = Quaternion.Euler(56f, 0f, 0f);
        cam.fieldOfView = 46f;
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
