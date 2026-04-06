using UnityEngine;

public class CapstoneFollowCamera : MonoBehaviour
{
    [SerializeField] private Transform target;
    [SerializeField] private Vector3 offset = new Vector3(0f, 16f, -18f);
    [SerializeField] private float followSmooth = 8f;
    [SerializeField] private float lookHeight = 1.4f;

    private bool snapToTargetOnNextFrame = true;

    public void Configure(Transform followTarget, Vector3 followOffset)
    {
        target = followTarget;
        offset = followOffset;
        snapToTargetOnNextFrame = true;
    }

    private void LateUpdate()
    {
        if (target == null)
        {
            return;
        }

        var desiredPosition = target.position + target.TransformDirection(offset);
        if (snapToTargetOnNextFrame)
        {
            transform.position = desiredPosition;
            snapToTargetOnNextFrame = false;
        }
        else
        {
            transform.position = Vector3.Lerp(
                transform.position,
                desiredPosition,
                followSmooth * Time.deltaTime
            );
        }

        transform.LookAt(target.position + new Vector3(0f, lookHeight, 0f));
    }
}
