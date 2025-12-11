import argparse, math
from kubernetes import client, config, watch

# TODO: load_client(kubeconfig) -> CoreV1Api
# - Use config.load_incluster_config() by default, else config.load_kube_config()
def load_client(kubeconfig):
    if kubeconfig:
        config.load_kube_config(config_file=kubeconfig)
    else:
        config.load_incluster_config()
    return client.CoreV1Api()

# TODO: bind_pod(api, pod, node_name)
# - Create a V1Binding with metadata.name=pod.name and target.kind=Node,target.name=node_name
# - Call api.create_namespaced_binding(namespace, body)
def bind_pod(api, pod, node_name):
    target = client.V1ObjectReference(
        kind="Node",
        name=node_name,
    )
    meta = client.V1ObjectMeta(name=pod.metadata.name)
    body = client.V1Binding(metadata=meta, target=target)

    api.create_namespaced_binding(
        namespace=pod.metadata.namespace,
        body=body,
        _preload_content=False,
    )
    print(f"[watch-scheduler] Bound {pod.metadata.namespace}/{pod.metadata.name} -> {node_name}", flush=True)

# TODO: choose_node(api, pod) -> str
# - List nodes and pick one based on a simple policy (fewest running pods)
def choose_node(api, pod):
    nodes = [n for n in api.list_node().items if "env" in (n.metadata.labels or {}) and n.metadata.labels["env"] == "prod"]
    
    if not nodes:
        return None

    pods = api.list_pod_for_all_namespaces().items

    min_cnt = math.inf
    pick = nodes[0].metadata.name

    for n in nodes:
        cnt = sum(1 for p in pods if p.spec.node_name == n.metadata.name)
        if cnt < min_cnt:
            min_cnt = cnt
            pick = n.metadata.name

    return pick


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scheduler-name", default="my-scheduler")
    parser.add_argument("--kubeconfig", default=None)
    args = parser.parse_args()
    # TODO: api = load_client(args.kubeconfig)
    api = load_client(args.kubeconfig)
    print(f"[watch-student] scheduler starting… name={args.scheduler_name}")
    w = watch.Watch()
    # Stream Pod events across all namespaces
    for evt in w.stream(client.CoreV1Api().list_pod_for_all_namespaces,_request_timeout=60):
        obj = evt['object']
        if obj is None or not hasattr(obj, 'spec'):
            continue
        # TODO: Only act on Pending pods that target our schedulerName
        # - if obj.spec.node_name is not set and obj.spec.scheduler_name == args.scheduler_name:
        # node = choose_node(api, obj)
        # bind_pod(api, obj, node)
        # print(...)
        if obj.spec.node_name is not set and obj.spec.scheduler_name == args.scheduler_name:
            print(f"[watch-scheduler] event={evt['type']} pod={obj.metadata.namespace}/{obj.metadata.name}")
            node = choose_node(api, obj)
            if not node:
                print(f"[scheduler] no hay nodos válidos para {pod.metadata.namespace}/{pod.metadata.name}",)
            else:
                bind_pod(api, obj, node)

if __name__ == "__main__":
    main()