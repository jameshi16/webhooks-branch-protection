from git import Repo, RemoteProgress
from git.objects.util import Actor
from functools import lru_cache
import json
import os

ENABLE_PR_PROGRESS_PRINTER = False # in multithreaded env, the printing isn't that pretty.
CACHE_FOLDER = ".cache"

class PRProgressPrinter(RemoteProgress):
	"""
	PRProgressPrinter is a progress printer for ProtectedRepository
	"""
	def update(self, op_code, cur_count, max_count=None, message=''):
		if ENABLE_PR_PROGRESS_PRINTER:
			print('\rOpCode: {: <2d} Current: {: <6.2f} Max: {: <6.2f} Percent: {: <7.2%}'.format(op_code, cur_count, max_count or 100.0, cur_count / (max_count or 100.0), message), end='\r')

class ProtectedRepository:
	"""
	ProtectedRepository is a lazy-loading protected repository object
	"""
	def __init__(self, name, path, url, branch):
		self.__repo = None
		self.__name = name
		self.__path = path
		self.__url = url
		self.__branch = branch

		self.__author = Actor("Branch Protection", "branch_protection@noreply.com")
		self.__committer = Actor("Branch Protection", "branch_protection@noreply.com")

	@property
	def name(self):
		return self.__name

	@property
	def branch(self):
		return self.__branch

	def set_committer(self, name, email):
		self.__committer = Actor(name, email)

	def set_author(self, name, email):
		self.__author = Actor(name, email)

	def clone_or_infer_repo(self):
		if not os.path.isdir(CACHE_FOLDER):
			print(".cache folder not found. creating...")
			os.mkdir(CACHE_FOLDER)

		if not os.path.isdir(self.__path):
			print("repository {:s} not found. cloning...".format(self.__name))
			self.__repo = Repo.clone_from(self.__url, self.__path, progress=PRProgressPrinter())
			if ENABLE_PR_PROGRESS_PRINTER:
				print() # make a new line

			origin = self.__repo.remote('origin')
			target_branch = self.__repo.create_head(self.__branch, origin.refs[self.__branch])
			self.__repo.head.set_reference(target_branch)
			return self.__repo

		print("repository inferred for {:s}".format(self.__name))
		self.__repo = Repo(self.__path)
		return self.__repo

	def get_repo(self):
		if self.__repo != None:
			return self.__repo

		return self.clone_or_infer_repo()

	@lru_cache(maxsize=1)
	def last_good_commit(self):
		repo = self.get_repo()
		commits_iter = repo.iter_commits(self.__branch)
		for commit in commits_iter:
			committer = commit.committer
			if committer.name == "GitHub" and committer.email == "noreply@github.com":
				return commit
			if committer.name == self.__committer.name and committer.email == self.__committer.email:
				return commit
		return None

	def pull(self):
		"""
		Internally force-pulls, since somebody can do a git push --force to ruin the current index.
		"""
		repo = self.get_repo()
		origin = repo.remote('origin')
		print("{:s}: pulling new changes".format(self.__path))
		origin.fetch(progress=PRProgressPrinter(), prune=True)
		if ENABLE_PR_PROGRESS_PRINTER:
			print() 
		repo.head.reset(origin.refs[self.__branch], index=True, working_tree=True)

		self.last_good_commit.cache_clear()	

	def push(self, commit):
		repo = self.get_repo()
		index = repo.index

		# softly reset the files
		print("{:s}: resetting files".format(self.__path))
		index.reset(commit, working_tree=True, head=False)

		# delete untracked files and directories
		print("{:s}: deleting untracked files".format(self.__path))
		untracked_files = repo.untracked_files
		extracted_directories = filter(lambda x: x != '', map(lambda x: os.path.dirname(x), untracked_files))

		for untracked_file in untracked_files:
			os.remove('/'.join([self.__path, untracked_file])) # slowly delete a folder

		for directory in sorted(extracted_directories, reverse=True): # reverse sort, longer pathnames => child of parent dir.
			rel_path_to_dir = '/'.join([self.__path, directory])
			if len(os.listdir(rel_path_to_dir)) == 0:
				os.removedirs(rel_path_to_dir)

		# create commit
		index.commit("(Branch Proteciton) Revert to {:s}".format(commit.hexsha), author=self.__author, committer=self.__committer)

		# push (ignore error, we'll handle that next time)
		origin = repo.remote('origin')
		results = origin.push(progress=PRProgressPrinter())
		for result in results:
			if result.flags & result.ERROR:
				print("error while pushing repository. flag: {:d}".format(result.flags))

		# pull for new changes
		self.pull()	
