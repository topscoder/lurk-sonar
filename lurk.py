import json
import os
import requests


# Reading settings
with open(".settings.json") as settings:
    data = json.load(settings)
    base_url = data["base_url"]
    username = data["username"]
    password = data["password"]


def write_file_in_dir(fullname, content, is_json=True):
    directorypath = ""
    filename = fullname
    if '/' in fullname:
        filename = os.path.basename(fullname)
        directorypath = fullname.replace(filename, "")

    try:
        os.makedirs(directorypath, exist_ok=True)
    except OSError as e:
        print(e)

    with open(os.path.join(directorypath, filename), "w+") as fp:
        to_write = json.dumps(content, indent=4) \
            if is_json is True \
            else content
        fp.write(to_write)

    return True


def update_progress(project="", file=""):
    progress = {
        "project": project,
        "file": file
    }
    with open("progress.rc", "w+") as f:
        f.write(json.dumps(progress, indent=4))


def get_progress():
    progress = json.loads('{ "project": "", "file": "" }')
    with open("progress.rc", "r") as f:
        content = f.read()
        if content != "":
            progress = json.loads(content)

    return progress


progress = get_progress()
if progress["project"] != "":
    resume = True
else:
    # Create with fresh progress file
    resume = False
    update_progress("")

# resume = False

# First get all projects
print("# Fetching all projects ...")
r = requests.get(f"{base_url}/api/projects/search", auth=(username, password))
js = r.json()

if resume is False:
    print("# Dump to projects.json ...")
    write_file_in_dir("lurked/projects.json", json.dumps(js, indent=4))

    update_progress("lurked/projects.json")

# For each project, get all filenames
print("# Download files for each project ...")
for key, value in js.items():
    if key != "components":
        continue

    for row in value:
        project_key = row.get("key")
        print("")

        if resume is True:
            if project_key == progress["project"]:
                print(f"[{project_key}] Resuming this project...")
                resume = False
            else:
                print(f"[{project_key}] Skipping {project_key}...")
                continue

        if resume is True and progress["file"] == "":
            resume = False

        print(f"## [{project_key}] Project {project_key}...")

        rp = requests.get(
            f"{base_url}/batch/project?key={project_key}", auth=(username, password))

        # write sources.json
        try:
            sources = rp.json()
        except Exception as e:
            print(f"### {project_key} ERROR Failed to parse project file.")
            print(f"Exception: {e}")
            print(rp.text)
            write_file_in_dir(f"lurked/{project_key}.failed", rp.text)
            continue

        if resume is False:
            print(f"## [{project_key}] Write lurked/{project_key}.json ...")
            write_file_in_dir(f"lurked/{project_key}.json", sources)
            update_progress(project_key, f"lurked/{project_key}.json")

        # get source code for each project file
        if "settingsByModule" in sources \
            and project_key in sources["settingsByModule"] \
                and "sonar.scm.provider" in sources["settingsByModule"][project_key]:
            print(f"## [{project_key}] Write lurked/{project_key}/scm.json ...")
            write_file_in_dir(f"lurked/{project_key}/scm.json", sources)
            continue

        if not sources["fileDataByModuleAndPath"] or not sources["fileDataByModuleAndPath"][project_key]:
            print(f"## [{project_key}] ERROR Unknown source structure ...")
            write_file_in_dir(f"lurked/{project_key}/source.json", sources)
            continue

        file_list = sources["fileDataByModuleAndPath"][project_key]
        for filename in file_list:
            if resume is True:
                if filename == progress["file"]:
                    print(f" [{project_key}]Resuming {filename}")
                    resume = False
                else:
                    print(f" [{project_key}]Skipping {filename}...")
                    continue

            # at this point, resume should always be False
            # if not, we should resume but couldnt find the right file.
            # so better is to start fresh.
            if resume is True:
                print(f"### [{project_key}] ERROR: We could not find the right file to resume from.")
                print("Please remove progress.rc and restart this script.")
                exit(1)

            # fetch source code and store in local file
            update_progress(project_key, filename)

            rs = requests.get(
                f"{base_url}/api/sources/index?key={project_key}&resource={project_key}:{filename}",
                auth=(username, password))

            if rs.status_code != 200:
                print(f"[{project_key}] --- PANIC AT THE DISCO 🪩")
                print(f"[{project_key}] --- HTTP {rs.status_code}")
                print(
                    f"[{project_key}] --- Error fetching {base_url}/api/sources/index?key={project_key} & resource={project_key}: {filename}")
                print(
                    f"[{project_key}] --- Skipping this one, but let's dance again..")
                continue

            if rs is None:
                print(f"[{project_key}] --- PANIC AT THE DISCO 🪩")
                print(f"[{project_key}] --- HTTP None")
                print(
                    f"[{project_key}] --- Error fetching {base_url}/api/sources/index?key={project_key} & resource={project_key}: {filename}")
                print(
                    f"[{project_key}] --- Skipping this one, but let's dance again..")
                continue

            file_lines = rs.json()
            file_str = ""
            for key in file_lines:
                for line in key:
                    file_str += key[line] + "\n"

            print(f"### [{project_key}] Writing {filename}")

            write_file_in_dir(
                os.path.join("lurked/", project_key, filename), file_str, is_json=False)


update_progress("DONE")
