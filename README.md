# bitbucket-to-github
Mirror script to migrate your repositories from bitbucket to github

## Usage

1. Clone this repository
1. Install dependencies with `pip install -r requirements.txt`
1. run the script with `python bitbucket-to-github.py`

## Tips

If you want to migrate only a specific repository, just create a file called `repos.txt` in the root of the project and add the name of the repository you want to migrate. The script will only migrate that repository.

If you don't want to get all your repositories, just comment the `listar_repositorios()` line in the script. This will make the script only migrate the repositories you have in the `repos.txt` file.