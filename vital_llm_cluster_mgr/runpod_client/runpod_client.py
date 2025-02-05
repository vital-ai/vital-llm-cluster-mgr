import requests

class RunpodClient:

    BASE_URL = "https://api.runpod.io/graphql"

    def __init__(self, runpod_api_key: str):
        self.runpod_api_key = runpod_api_key

    def _post(self, payload: dict) -> dict:
        """
        Helper method to send a POST request to the Runpod GraphQL endpoint.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.runpod_api_key}"
        }
        response = requests.post(self.BASE_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Request failed with status code {response.status_code}: {response.text}")

    def get_gpu_prices(self):
        query = """
            query GpuTypes {
                gpuTypes {
                    id
                    displayName
                    memoryInGb
                    securePrice
                    communityPrice
                    secureSpotPrice
                    communitySpotPrice
                }
            }
        """
        data = self._post({"query": query})
        # (Optional) Print the full response for debugging
        # print(data)
        try:
            return data["data"]["gpuTypes"]
        except KeyError:
            raise Exception("Unexpected response format: " + str(data))

    def get_gpu_ids(self):
        """
        Returns a list of available GPU IDs by extracting them from the gpuTypes query.
        """
        gpu_types = self.get_gpu_prices()
        return [gpu["id"] for gpu in gpu_types]

    def get_running_pods(self):
        """
        Retrieves a list of currently running pods with their status, resource usage, and network details.

        Returns:
            list[dict]: A list of pods, each containing details such as ID, name, uptime, ports, GPU usage, and container stats.
        """
        query = """
        query Pods {
            myself {
                pods {
                    id
                    name
                    runtime {
                        uptimeInSeconds
                        ports {
                            ip
                            isIpPublic
                            privatePort
                            publicPort
                            type
                        }
                        gpus {
                            id
                            gpuUtilPercent
                            memoryUtilPercent
                        }
                        container {
                            cpuPercent
                            memoryPercent
                        }
                    }
                }
            }
        }
        """

        data = self._post({"query": query})

        try:
            return data["data"]["myself"]["pods"]
        except KeyError:
            raise Exception("Unexpected response format: " + str(data))

    def get_pod_details(self, pod_id: str):
        """
        Retrieves detailed information about a specific pod by its ID.

        Args:
            pod_id (str): The ID of the pod.

        Returns:
            dict: A dictionary containing the pod's details, including ID, name, uptime, ports, GPU usage, and container stats.
        """
        query = """
        query Pod($input: PodFilter!) {
            pod(input: $input) {
                id
                name
                runtime {
                    uptimeInSeconds
                    ports {
                        ip
                        isIpPublic
                        privatePort
                        publicPort
                        type
                    }
                    gpus {
                        id
                        gpuUtilPercent
                        memoryUtilPercent
                    }
                    container {
                        cpuPercent
                        memoryPercent
                    }
                }
            }
        }
        """

        variables = {"input": {"podId": pod_id}}

        print(query, variables)

        data = self._post({"query": query, "variables": variables})

        try:
            return data["data"]["pod"]
        except KeyError:
            raise Exception(f"Unexpected response format: {data}")

    def start_pod(self, template_id: str, gpu_id: str, on_demand: bool):
        """
        Starts a RunPod instance using the specified template and GPU type.

        Args:
            template_id (str): The ID of the pod template to use.
            gpu_id (str): The GPU type ID (as retrieved from `get_gpu_prices`).
            on_demand (bool): If True, deploys on-demand; if False, uses a spot instance.

        Returns:
            dict: The response containing the pod's details.
        """
        mutation_name = "podFindAndDeployOnDemand" if on_demand else "podRentInterruptable"

        mutation = f"""
        mutation StartPod($input: PodFindAndDeployOnDemandInput!) {{
            {mutation_name}(input: $input) {{
                id
                imageName
                env
                machineId
                machine {{
                    podHostId
                }}
            }}
        }}
        """ if on_demand else f"""
        mutation StartPod($input: PodRentInterruptableInput!) {{
            {mutation_name}(input: $input) {{
                id
                imageName
                env
                machineId
                machine {{
                    podHostId
                }}
            }}
        }}
        """

        input_data = {
            "cloudType": "ALL" if on_demand else "SECURE",
            "gpuCount": 1,
            "volumeInGb": 40,
            "containerDiskInGb": 200,
            # "minVcpuCount": 2,
            # "minMemoryInGb": 15,
            "gpuTypeId": gpu_id,  # Ensure this is the correct ID from `get_gpu_prices()`
            "name": template_id,  # Verify this matches an available template ID
            # "imageName": template_id,  # Double-check the template name
            "templateId": template_id,
            "dockerArgs": "",
            "ports": "8888/http",
            "volumeMountPath": "/workspace",
            # "env": [{"key": "JUPYTER_PASSWORD", "value": "securepassword123"}]  # Change if necessary
        }

        data = self._post({"query": mutation, "variables": {"input": input_data}})
        try:
            return data["data"][mutation_name]
        except KeyError:
            raise Exception(f"Unexpected response format: {data}")

    def stop_pod(self, pod_id: str):
        """
        Stops a running pod by its ID.

        Args:
            pod_id (str): The ID of the pod to stop.

        Returns:
            dict: The response containing the pod's ID and desired status after stopping.
        """
        mutation = """
        mutation StopPod($input: PodStopInput!) {
            podStop(input: $input) {
                id
                desiredStatus
            }
        }
        """

        variables = {"input": {"podId": pod_id}}  # ✅ Correct: Uses "PodFilter!" instead of "PodInput!"

        # print(mutation, variables)

        data = self._post({"query": mutation, "variables": variables})

        try:
            return data["data"]["podStop"]
        except KeyError:
            raise Exception(f"Unexpected response format: {data}")

    def terminate_pod(self, pod_id: str):
        """
        Terminates a pod by its ID.

        Args:
            pod_id (str): The ID of the pod to terminate.

        Returns:
            bool: True if the termination request was successful, False otherwise.
        """
        mutation = """
        mutation TerminatePod($input: PodTerminateInput!) {
            podTerminate(input: $input)
        }
        """

        variables = {"input": {"podId": pod_id}}  # ✅ Correct: Uses "PodFilter!" instead of "PodTerminateInput!"

        data = self._post({"query": mutation, "variables": variables})

        try:
            # If the response contains "podTerminate": null, it means the termination was successful
            return data["data"]["podTerminate"] is None
        except KeyError:
            raise Exception(f"Unexpected response format: {data}")

    def get_pod_templates(self):
        """
        Retrieves a list of available pod templates.
        """
        query = """
        query Myself {
            myself {
                podTemplates {
                    id
                    name
                    imageName
                    isPublic
                }
            }
        }
        """
        data = self._post({"query": query})
        try:
            return data["data"]["myself"]["podTemplates"]
        except KeyError:
            raise Exception("Unexpected response format: " + str(data))

