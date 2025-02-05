import time
from vital_llm_cluster_mgr.config.cluster_mgr_config import ClusterMgrConfig
from vital_llm_cluster_mgr.runpod_client.runpod_client import RunpodClient

def main():

    config_file_path = "../vital-llm-cluster-mgr-config.yaml"

    config = ClusterMgrConfig(config_file_path)

    runpod_api_key = config.runpod_key

    runpod_client = RunpodClient(runpod_api_key)

    gpu_list = runpod_client.get_gpu_prices()

    print(
        f"{'GPU ID':<40}{'GPU Type':<25}{'Memory (GB)':<12}{'Secure Price ($/hr)':<22}{'Community Price ($/hr)':<25}{'Secure Spot Price ($/hr)':<25}{'Community Spot Price ($/hr)':<25}")
    print("=" * 175)
    for gpu in gpu_list:
        print(f"{gpu['id']:<40}{gpu['displayName']:<25}{gpu['memoryInGb']:<12}"
              f"{str(gpu.get('securePrice', 'N/A') or 'N/A'):<22}"
              f"{str(gpu.get('communityPrice', 'N/A') or 'N/A'):<25}"
              f"{str(gpu.get('secureSpotPrice', 'N/A') or 'N/A'):<25}"
              f"{str(gpu.get('communitySpotPrice', 'N/A') or 'N/A'):<25}")

    pod_templates = runpod_client.get_pod_templates()

    for pod_tmp in pod_templates:
        print(pod_tmp)

    running_pods = runpod_client.get_running_pods()

    print(running_pods)

    for pod in running_pods:
        print(pod)

    # 'id': 'w0vokfjnj6', 'name': 'vital-llm-reasoner-server'

    # "NVIDIA A40"

    gpu_id = "NVIDIA A40"
    template_id = "w0vokfjnj6"
    on_demand = True


    print(f"Starting pod with GPU ID: {gpu_id} and Template ID: {template_id} (On-Demand: {on_demand})...")
    pod_info = runpod_client.start_pod(template_id, gpu_id, on_demand)
    pod_id = pod_info["id"]
    print(f"Pod started with ID: {pod_id}")

    running_pods = runpod_client.get_running_pods()

    print(running_pods)

    print(f"Stopping pod {pod_id}...")
    runpod_client.stop_pod(pod_id)

    running_pods = runpod_client.get_running_pods()

    print(running_pods)

    print(f"Terminating pod {pod_id}...")
    runpod_client.terminate_pod(pod_id)

    running_pods = runpod_client.get_running_pods()

    print(running_pods)

    exit(0)

    # Step 2: Poll until Pod is Running
    print(f"Polling for pod {pod_id} to reach 'RUNNING' status...")
    while True:
        pod_details = runpod_client.get_pod_details(pod_id)

        runtime = pod_details.get("runtime")

        if runtime is not None:
            pod_status = pod_details.get("runtime", {}).get("uptimeInSeconds", None)

            if pod_status is not None:
                print(f"Pod {pod_id} is now RUNNING. Uptime: {pod_status} seconds.")
                break

        print(f"Pod {pod_id} is still starting... Retrying in 5 seconds.")
        time.sleep(5)

    # Step 3: Wait 30 seconds before stopping
    print(f"Waiting 30 seconds before stopping pod {pod_id}...")
    time.sleep(30)

    # Step 4: Stop the Pod
    print(f"Stopping pod {pod_id}...")
    runpod_client.stop_pod(pod_id)

    # Step 5: Wait 30 seconds before terminating
    print(f"Waiting 30 seconds before terminating pod {pod_id}...")
    time.sleep(30)

    # Step 6: Terminate the Pod
    print(f"Terminating pod {pod_id}...")
    runpod_client.terminate_pod(pod_id)

    pod_terminated = False

    # Step 7: Poll until Pod is fully Terminated
    print(f"Polling to confirm pod {pod_id} is terminated...")
    for _ in range(10):  # Retry up to 10 times
        running_pods = runpod_client.get_running_pods()
        pod_ids = {p["id"] for p in running_pods}

        if pod_id not in pod_ids:
            print(f"Pod {pod_id} has been successfully terminated.")
            pod_terminated = True
            break

        print(f"Pod {pod_id} is still present. Retrying in 5 seconds...")
        time.sleep(5)

    if not pod_terminated:
        print(f"Pod {pod_id} may not have terminated properly.")


if __name__ == "__main__":
    main()
