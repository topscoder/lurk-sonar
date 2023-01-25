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


def update_progress(value):
    with open("progress.rc", "w+") as f:
        f.write(value)


def get_progress():
    progress = ""
    with open("progress.rc", "w+") as f:
        progress = f.read()
    return progress


# Create with fresh progress file
update_progress("")

# First get all projects
print("# Fetching all projects ...")
r = requests.get(f"{base_url}/api/projects/search", auth=(username, password))
js = r.json()

print("# Dump to projects.json ...")
with open("lurked/projects.json", "w+") as f:
    f.write(json.dumps(js, indent=4))

update_progress("lurked/projects.json")

# For each project, get all filenames
print("# Fetch files for each project ...")
for key, value in js.items():
    if key != "components":
        continue

    for row in value:
        project_key = row.get("key")
        print("")
        print(f"## Project {project_key}...")

        rp = requests.get(
            f"{base_url}/batch/project?key={project_key}", auth=(username, password))

        # write sources.json
        print(f"## Write lurked/{project_key}.json ...")
        sources = rp.json()
        write_file_in_dir(f"lurked/{project_key}.json", sources)

        update_progress(f"lurked/{project_key}.json")

        # get source code for each project file
        file_list = sources["fileDataByModuleAndPath"][project_key]
        for filename in file_list:
            # fetch source code and store in local file
            update_progress(f"project:{project_key}\nfilename:{filename}")

            rs = requests.get(
                f"{base_url}/api/sources/index?key={project_key}&resource={project_key}:{filename}",
                auth=(username, password))

            if rs.status_code != 200:
                print(f"--- PANIC AT THE DISCO 🪩")
                print(f"--- HTTP {rs.status_code}")
                print(f"--- Error fetching {base_url}/api/sources/index?key={project_key} & resource={project_key}: {filename}")
                print(f"--- Skipping this one, but let's dance again..")
                continue

            if rs is None:
                print(f"--- PANIC AT THE DISCO 🪩")
                print(f"--- HTTP None")
                print(
                    f"--- Error fetching {base_url}/api/sources/index?key={project_key} & resource={project_key}: {filename}")
                print(f"--- Skipping this one, but let's dance again..")
                continue

            file_lines = rs.json()
            file_str = ""
            for key in file_lines:
                for line in key:
                    file_str += key[line] + "\n"

            print(f"### Writing {filename}")

            write_file_in_dir(
                os.path.join("lurked/", project_key, filename), file_str, is_json=False)


update_progress("DONE")
