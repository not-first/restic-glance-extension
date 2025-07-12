# Restic Glance Extension
_An extension widget API for the [Glance](https://github.com/glanceapp/glance) dashboard._

![Widget screenshot](https://github.com/user-attachments/assets/15b0dc61-6328-4222-8282-ec64691a239b)

A simple widget that shows information about the latest snapshot in a restic repo.
Displays the short ID of the latest snapshot, and the time it was created in a human readable form. Also includes general information about the repo.
Optionally, if [autorestic](https://autorestic.vercel.app/) is being used to back up it can show a small icon to indicate whether the backup was automatic or manual.

## Setup
### Docker Compose
Add the following to your existing glance docker compose
```yml
services:
  glance:
    image: glanceapp/glance
    # ...

  restic-glance-extension:
    image: ghcr.io/not-first/restic-glance-extension
    ports:
      - '8675:8675'
    volumes:
      - /my/backup/location/repo1:/app/repos/repo1
      - /my/backup/location/repo2-different-name:/app/repos/repo1
    restart: unless-stopped
    env_file: .env
```
#### Environment Variables
This widget must be set up be providing environment variables, which can be added to your existing glance .env file. A full environment file might look like this:
```env
RESTIC_REPOS=repo1,repo2

REPO1_RESTIC_PASSWORD=mypassword1

REPO2_RESTIC_ENV__GOOGLE_APPLICATION_CREDENTIALS=app/config/credentials.json
REPO2_RESTIC_URL=gs:be18b21d-4de1-4a41-a6dc-20a51251b058-repo2:repo2
REPO2_RESTIC_PASSWORD=mypassword2

RESTIC_CACHE_INTERVAL=3600
```

The `REPOS` variable must contain comma seperated list of repo aliases, which are simple names you assign to allow the program to differentiate between repos. Additional configuration for the alias can be supplied with an environment variable starting with `{PREFIX}_RESTIC_`, where `{PREFIX}` is the capitalised alias of the repo.
  - `{PREFIX}_RESTIC_PASSWORD`: the password for the repo (required)
  - `{PREFIX}_RESTIC_URL`: for restic operations, the repo url will be `/app/repos/{alias}`. This env var can be used to replace the url entirely
  - `{PREFIX}_RESTIC_ENV__{MY_ENV_VAR}`: any env var provided in this format will be passed down to any restic commands run on that repo, with the `{PREFIX}_RESTIC_ENV__` part of the name removed

Local repos must have a corresponding volume mount to the folder `/app/repos/{alias}`. See the provided .env.example and docker-compose.yml file above for a simple example.
Note that this alias does not have to correspond to the name of the repo folder on your machine. **Just where it is mounted to.**

`REPOS_BASE_PATH` can be set to change the base directory from `/app/repos`, so the local repo urls will be computed as `{REPOS_BASE_PATH}/{alias}`.

`RESTIC_CACHE_INTERVAL` can be set to a time in seconds, where the cache will be updated with the repo info every interval. _If not supplied it defaults to 3600 (1 hour)._
  - When the cache is updated, it fetches the restic repo stats and snapshot info. The humanised time difference is calculated for each request.

`RESTIC_REPOS_MODE` can be set to specify the mode for the `restic stats` command. Valid values are:
  - `restore-size` (default)
  - `files-by-contents`
  - `raw-data`
  - `blobs-per-file`

### Glance Config
Next, add the extension widget into your glance page by adding this to your `glance.yml`.
```yml
- type: extension
  title: My Backups
  url: http://restic-extension:8675/{repo-alias}
  cache: 1s # set to any time of your choice.
  allow-potentially-dangerous-html: true
```
The endpoint for your restic repo is accessible on the path `/{repo-alias}`, where `{repo-alias}` is the alias set for the repo in your .env file. In the example .env above, `/repo1` or `/repo2` would be used.

#### Parameters (all optional)
```yml
parameters:
  autorestic-icon: true
  hide-file-count: true
  limit: 1
```

`autorestic-icon`: An icon can be shown to indicate the method of backup (manual or cron). Give a value of 'true' to render it.
This is detected using the tags that [autorestic](https://autorestic.vercel.app/) applies to snapshots, therefore using autorestic to manage the repo is required.

`hide-file-count`: Set to 'true' to hide the file count from the widget, showing only the number of snapshots and total size.

`limit`: The number of snapshots to render. Snapshots before the most recent one will render in a compressed list. _See example below with limit set to 3_

![Example of widget with limit parameter set to 3](https://github.com/user-attachments/assets/26bf76ba-9c57-431d-94a0-f9516941dcdb)

---
