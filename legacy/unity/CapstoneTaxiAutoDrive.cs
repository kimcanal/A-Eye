using UnityEngine;

public class CapstoneTaxiAutoDrive : MonoBehaviour
{
    [SerializeField] private Vector3[] worldWaypoints = new Vector3[0];
    [SerializeField] private float moveSpeed = 4.5f;
    [SerializeField] private float turnSpeed = 6f;
    [SerializeField] private float waypointTolerance = 0.3f;
    [SerializeField] private bool loopRoute = true;
    [SerializeField] private bool attachFollowCamera;
    [SerializeField] private bool showMotionBeacon;

    private static bool mainCameraAssigned;
    private int currentWaypointIndex;
    private const string MotionBeaconName = "MotionBeacon";

    public void Configure(Vector3[] waypoints, float speed, bool enableFollowCamera = false, bool enableMotionBeacon = false)
    {
        worldWaypoints = waypoints ?? new Vector3[0];
        moveSpeed = speed;
        currentWaypointIndex = 0;
        attachFollowCamera = enableFollowCamera;
        showMotionBeacon = enableMotionBeacon;
    }

    private void Start()
    {
        if (worldWaypoints == null || worldWaypoints.Length == 0)
        {
            Debug.LogWarning($"Auto-drive has no waypoints on {name}");
            return;
        }

        if (showMotionBeacon)
        {
            EnsureVisualAid();
        }
        else
        {
            RemoveVisualAid();
        }
        Debug.Log($"Auto-drive started on {name} with {worldWaypoints.Length} waypoint(s)");
        if (attachFollowCamera)
        {
            TryAttachMainCamera();
        }
    }

    private void Update()
    {
        if (worldWaypoints == null || worldWaypoints.Length == 0)
        {
            return;
        }

        var target = worldWaypoints[currentWaypointIndex];
        var flatTarget = new Vector3(target.x, transform.position.y, target.z);
        var toTarget = flatTarget - transform.position;

        if (toTarget.magnitude <= waypointTolerance)
        {
            AdvanceWaypoint();
            return;
        }

        var lookDirection = toTarget.normalized;
        if (lookDirection.sqrMagnitude > 0.0001f)
        {
            var targetRotation = Quaternion.LookRotation(lookDirection, Vector3.up);
            transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, turnSpeed * Time.deltaTime);
        }

        transform.position = Vector3.MoveTowards(
            transform.position,
            flatTarget,
            moveSpeed * Time.deltaTime
        );
    }

    private void AdvanceWaypoint()
    {
        if (worldWaypoints == null || worldWaypoints.Length == 0)
        {
            return;
        }

        if (currentWaypointIndex < worldWaypoints.Length - 1)
        {
            currentWaypointIndex += 1;
            return;
        }

        if (loopRoute)
        {
            currentWaypointIndex = 0;
        }
    }

    private void TryAttachMainCamera()
    {
        if (mainCameraAssigned)
        {
            return;
        }

        var mainCam = ResolveFollowCamera();
        if (mainCam == null)
        {
            Debug.LogWarning($"No camera found for follow on {name}");
            return;
        }

        var follow = mainCam.GetComponent<CapstoneFollowCamera>();
        if (follow == null)
        {
            follow = mainCam.gameObject.AddComponent<CapstoneFollowCamera>();
        }

        follow.Configure(transform, new Vector3(0f, 16f, -18f));
        mainCameraAssigned = true;
        Debug.Log($"Attached main camera follow to {name}");
    }

    private void EnsureVisualAid()
    {
        if (transform.Find(MotionBeaconName) == null)
        {
            var beacon = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            beacon.name = MotionBeaconName;
            beacon.transform.SetParent(transform, false);
            beacon.transform.localPosition = new Vector3(0f, 4.5f, 0f);
            beacon.transform.localScale = new Vector3(3.2f, 3.2f, 3.2f);

            var beaconRenderer = beacon.GetComponent<Renderer>();
            if (beaconRenderer != null)
            {
                var beaconMaterial = new Material(Shader.Find("Standard"));
                beaconMaterial.color = new Color(1f, 0.55f, 0.1f);
                beaconMaterial.EnableKeyword("_EMISSION");
                beaconMaterial.SetColor("_EmissionColor", new Color(1f, 0.45f, 0.05f) * 1.4f);
                beaconRenderer.sharedMaterial = beaconMaterial;
            }
        }

        var trail = GetComponent<TrailRenderer>();
        if (trail != null)
        {
            Destroy(trail);
        }
    }

    private void RemoveVisualAid()
    {
        var existing = transform.Find(MotionBeaconName);
        if (existing != null)
        {
            DestroyImmediate(existing.gameObject);
        }
    }

    private Camera ResolveFollowCamera()
    {
        if (Camera.main != null)
        {
            return Camera.main;
        }

        var cameras = FindObjectsOfType<Camera>();
        foreach (var cam in cameras)
        {
            if (cam != null && cam.enabled && cam.gameObject.activeInHierarchy)
            {
                return cam;
            }
        }

        return null;
    }
}
