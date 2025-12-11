import argparse, math, time
from kubernetes import client, config, watch
from kubernetes.client.exceptions import ApiException

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

    backoff = 0.5
    max_retries = 3

    retries_counter=0 #For simulation

    for attempt in range(1, max_retries + 1):
        try:
            if retries_counter < 2:
                retries_counter += 1
                raise ApiException(status=500, reason="Simulated internal error")
                
            resp = api.create_namespaced_binding(
                namespace=pod.metadata.namespace,
                body=body,
                _preload_content=False)
            print(
                f"[watch-scheduler] bind OK {pod.metadata.namespace}/{pod.metadata.name} "
                f"-> {node_name} (attempt={attempt})")
            return
        except ApiException as e:
            # Errores transitorios típicos
            if e.status in (429, 500, 502, 503, 504):
                print(
                    f"[watch-scheduler] transient error in bind attempt={attempt}: "
                    f"status={e.status} reason={e.reason}")
                if attempt == max_retries:
                    print("[watch-scheduler] max retries reached, giving up", flush=True)
                    raise
                time.sleep(backoff)
                backoff *= 2
                continue
            # Errores no transitorios → re-lanzar
            print(
                f"[watch-scheduler] non-retryable ApiException: {e.status} {e.reason}")
            raise
        except Exception as e:
            print(f"[watch-scheduler] unexpected exception in bind: {e}")
            raise

# TODO: choose_node(api, pod) -> str
# - List nodes and pick one based on a simple policy (fewest running pods)
def choose_node(api, pod):
    nodes = api.list_node().items
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
        if obj.spec.node_name is None and obj.spec.scheduler_name == args.scheduler_name:
            print(f"[watch-scheduler] event={evt['type']} pod={obj.metadata.namespace}/{obj.metadata.name}")
            node = choose_node(api, obj)
            if not node:
                print(f"[scheduler] no hay nodos válidos para {pod.metadata.namespace}/{pod.metadata.name}",)
            else:
                bind_pod(api, obj, node)
if __name__ == "__main__":
    main()