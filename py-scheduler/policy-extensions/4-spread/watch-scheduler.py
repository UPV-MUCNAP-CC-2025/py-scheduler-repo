import argparse, math
from kubernetes import client, config, watch

def load_client(kubeconfig):
    if kubeconfig:
        config.load_kube_config(config_file=kubeconfig)
    else:
        config.load_incluster_config()
    return client.CoreV1Api()

# TODO: load_client(kubeconfig) -> CoreV1Api
# - Use config.load_incluster_config() by default, else config.load_kube_config()

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

# TODO: bind_pod(api, pod, node_name)
# - Create a V1Binding with metadata.name=pod.name and target.kind=Node,target.name=node_name
# - Call api.create_namespaced_binding(namespace, body)

def choose_node(api, pod):
    nodes = api.list_node().items
    pods = api.list_pod_for_all_namespaces().items

    app_label = (pod.metadata.labels or {}).get("app")

    best_node = nodes[0].metadata.name
    best_score = math.inf

    for n in nodes:
        node_name = n.metadata.name

        if app_label:
            # contar solo pods con la misma app
            same_app_count = sum(
                1 for p in pods
                if p.spec.node_name == node_name
                and (p.metadata.labels or {}).get("app") == app_label
            )
            score = same_app_count
        else:
            # fallback: contar todos los pods del nodo
            total_count = sum(
                1 for p in pods
                if p.spec.node_name == node_name
            )
            score = total_count

        print(
            f"[watch-scheduler] node {node_name} score={score} "
            f"(app={app_label})"
        )

        if score < best_score:
            best_score = score
            best_node = node_name

    print(f"[watch-scheduler] choosing node {best_node} with score={best_score}")
    return best_node



# TODO: choose_node(api, pod) -> str
# - List nodes and pick one based on a simple policy (fewest running pods)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scheduler-name", default="my-scheduler")
    parser.add_argument("--kubeconfig", default=None)
    args = parser.parse_args()
    api = load_client(args.kubeconfig)
    # TODO: api = load_client(args.kubeconfig)
    print(f"[watch-student] scheduler starting… name={args.scheduler_name}")
    w = watch.Watch()
    # Stream Pod events across all namespaces
    for evt in w.stream(client.CoreV1Api().list_pod_for_all_namespaces,_request_timeout=60):
        obj = evt['object']
        if obj is None or not hasattr(obj, 'spec'):
            continue
        if evt["type"] != "ADDED":
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