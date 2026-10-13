"""Manage the RunPod GPU pod that runs MiniMax H3 (ComfyUI).
Usage: python tools/runpod_pod.py create|status|stop|start|terminate
Needs RUNPOD_API_KEY in .env. The pod id is remembered in .runpod_pod (gitignored via .env.* is not enough, so see .gitignore).
SSH: python tools/runpod_pod.py status prints the ssh command (key: ~/.ssh/runpod_lyra).
"""
import json, os, pathlib, sys, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
env = {}
for line in open(ROOT / ".env", encoding="utf-8-sig"):
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1); env[k.strip()] = v.strip()
STATE = ROOT / ".runpod_pod"
GPU = "NVIDIA RTX PRO 6000 Blackwell Server Edition"
IMAGE = "runpod/pytorch:1.4.1-rc.177-cu1290-torch291-ubuntu2404"

def gql(q, variables=None):
    req = urllib.request.Request("https://api.runpod.io/graphql",
        data=json.dumps({"query": q, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + env["RUNPOD_API_KEY"],
                 "User-Agent": "lyra-movie/1.0"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read()[:500]}")
    if d.get("errors"): sys.exit(json.dumps(d["errors"], indent=1))
    return d["data"]

def pod_id():
    if not STATE.exists(): sys.exit("no pod recorded in .runpod_pod")
    return STATE.read_text().strip()

cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
if cmd == "create":
    if STATE.exists(): sys.exit(f"pod already recorded: {STATE.read_text().strip()}")
    pub = (pathlib.Path.home() / ".ssh" / "runpod_lyra.pub").read_text().strip()
    d = gql("""mutation($i: PodFindAndDeployOnDemandInput) { podFindAndDeployOnDemand(input: $i) {
              id costPerHr machine { gpuDisplayName location } } }""",
        {"i": {"cloudType": os.environ.get("RP_CLOUD", "COMMUNITY"), "gpuCount": 1, "gpuTypeId": GPU, "name": "lyra-h3",
               "imageName": IMAGE, "containerDiskInGb": 150, "volumeInGb": 0,
               "minVcpuCount": 8, "minMemoryInGb": int(os.environ.get("RP_RAM", "64")), "ports": "8188/http,22/tcp",
               "env": [{"key": "PUBLIC_KEY", "value": pub}],
               **({"dataCenterId": os.environ["RP_DC"]} if os.environ.get("RP_DC") else {})}})
    p = d["podFindAndDeployOnDemand"]
    STATE.write_text(p["id"]); print(json.dumps(p, indent=1))
elif cmd == "status":
    d = gql("""query($id: String!) { pod(input: {podId: $id}) { id name desiredStatus costPerHr uptimeSeconds
              machine { gpuDisplayName location } runtime { uptimeInSeconds ports { ip isIpPublic privatePort publicPort type } } } }""",
        {"id": pod_id()})
    p = d["pod"]; print(json.dumps(p, indent=1))
    for pt in ((p.get("runtime") or {}).get("ports") or []):
        if pt["privatePort"] == 22 and pt["isIpPublic"]:
            print(f'\nssh -i ~/.ssh/runpod_lyra -p {pt["publicPort"]} root@{pt["ip"]}')
    print(f'ComfyUI: https://{p["id"]}-8188.proxy.runpod.net')
elif cmd == "stop":
    print(gql('mutation($id: String!) { podStop(input: {podId: $id}) { id desiredStatus } }', {"id": pod_id()}))
elif cmd == "start":
    print(gql('mutation($id: String!) { podResume(input: {podId: $id, gpuCount: 1}) { id desiredStatus costPerHr } }', {"id": pod_id()}))
elif cmd == "up":
    # resume the pod, then relaunch ComfyUI inside it and wait until it answers
    import subprocess, time
    d = gql('query($id: String!) { pod(input: {podId: $id}) { desiredStatus } }', {"id": pod_id()})
    if d["pod"]["desiredStatus"] != "RUNNING":
        print(gql('mutation($id: String!) { podResume(input: {podId: $id, gpuCount: 1}) { id desiredStatus costPerHr } }', {"id": pod_id()}))
    ssh = None
    for _ in range(80):
        p = gql("""query($id: String!) { pod(input: {podId: $id}) { runtime { ports { ip isIpPublic privatePort publicPort } } } }""",
                {"id": pod_id()})["pod"]
        ports = ((p.get("runtime") or {}).get("ports") or [])
        pt = next((x for x in ports if x["privatePort"] == 22 and x["isIpPublic"]), None)
        if pt:
            ssh = ["ssh", "-i", str(pathlib.Path.home() / ".ssh" / "runpod_lyra"), "-p", str(pt["publicPort"]),
                   "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=20", f'root@{pt["ip"]}']
            if subprocess.run(ssh + ["true"], capture_output=True).returncode == 0: break
        time.sleep(15)
    else:
        sys.exit("pod did not come up with SSH")
    # bootstrap is idempotent: on a fresh pod it installs everything, on a resumed pod it just relaunches ComfyUI
    subprocess.run(ssh + ["cat > /root/pod_bootstrap.sh"], input=(ROOT / "tools" / "pod_bootstrap.sh").read_bytes(), check=True)
    subprocess.run(ssh + ["bash /root/pod_bootstrap.sh > /root/bootstrap.log 2>&1; tail -3 /root/bootstrap.log"], check=True)
    url = f"https://{pod_id()}-8188.proxy.runpod.net/system_stats"
    for _ in range(60):
        try:
            urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 lyra-movie"}), timeout=15)
            print("ComfyUI is up:", url.rsplit("/", 1)[0]); print("ssh:", " ".join(ssh)); break
        except Exception:
            time.sleep(10)
    else:
        sys.exit("ComfyUI did not answer; check /workspace/comfy.log on the pod")
elif cmd == "terminate":
    gql('mutation($id: String!) { podTerminate(input: {podId: $id}) }', {"id": pod_id()})
    STATE.unlink(); print("terminated")
else:
    sys.exit(__doc__)
