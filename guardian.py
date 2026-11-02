import docker
import time
import os
import tarfile
import logging
from datetime import datetime

BACKUP_DIR = "/root/docker_backups"
MAX_BACKUPS = 3
EXCLUDE_CONTAINERS = ["mysql", "mariadb", "postgres"]

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("DockerGuardian")

def clean_old_backups(container_name):
    try:
        files = [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.startswith(f"{container_name}_")]
        files.sort(key=os.path.getmtime)
        while len(files) >= MAX_BACKUPS: os.remove(files.pop(0))
    except: pass

def backup_volumes(container):
    binds = container.attrs['HostConfig']['Binds'] or []
    if not binds: return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{BACKUP_DIR}/{container.name}_{timestamp}.tar.gz"
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with tarfile.open(backup_file, "w:gz") as tar:
            for bind in binds:
                host_path = bind.split(':')[0]
                if os.path.exists(host_path): tar.add(host_path, arcname=os.path.basename(host_path))
        clean_old_backups(container.name)
        return backup_file
    except: return None

def safe_update(client, container, new_image):
    old_image_id = container.image.id
    c_name = container.name
    backup_volumes(container)
    old_config = container.attrs
    ports = old_config['HostConfig']['PortBindings']
    binds = old_config['HostConfig']['Binds']
    container.stop(); container.remove()
    new_container = None
    try:
        new_container = client.containers.run(new_image.tags[0], name=c_name, detach=True, ports=ports, volumes=binds, restart_policy={"Name": "always"})
        time.sleep(10); new_container.reload()
        if new_container.status != 'running': raise Exception("Failed")
        logger.info(f"[{c_name}] Update success.")
    except Exception as e:
        logger.error(f"[{c_name}] Error. Rolling back...")
        if new_container:
            try: new_container.remove(force=True)
            except: pass
        try:
            client.containers.run(old_image_id, name=c_name, detach=True, ports=ports, volumes=binds, restart_policy={"Name": "always"})
            logger.info(f"[{c_name}] Rollback success.")
        except: pass

if __name__ == "__main__":
    client = docker.from_env()
    for c in client.containers.list():
        if c.name in EXCLUDE_CONTAINERS: continue
        image = c.image
        if not image.tags: continue
        image_tag = next((t for t in image.tags if t.endswith(':latest')), image.tags[0])
        repo, tag = image_tag.split(':') if ':' in image_tag else (image_tag, 'latest')
        try:
            new_image = client.images.pull(repo, tag=tag)
            if new_image.id != image.id: safe_update(client, c, new_image)
        except: pass