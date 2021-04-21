from git import Repo


class GITUtils(object):

    def __init__(self):
        self.repo = Repo(search_parent_directories=True)

    def get_repo_details(self):
        return {
            "remote_url": self.repo.remotes.origin.url,
            "active_branch": self.repo.active_branch.name,
            "commit_id": self.repo.head.object.hexsha
        }

    def get_diff(self):
        return self.repo.git.diff('HEAD~1')

    def write_diff(self, outfile):
        f = open(outfile, "a")
        f.write(self.get_diff())
        f.close()


if __name__ == "__main__":
    git_obj = GITUtils()
    print(git_obj.get_repo_details())
    # print(git_obj.get_diff())
