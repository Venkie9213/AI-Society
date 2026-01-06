#!/usr/bin/env python3
"""
Repository Creation Tool
This script allows you to create GitHub repositories programmatically.
"""

import os
import sys
import argparse
from typing import Optional, Dict, Any
from github import Github, GithubException
from dotenv import load_dotenv


class RepositoryCreator:
    """Class to handle GitHub repository creation."""
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize the RepositoryCreator.
        
        Args:
            access_token: GitHub personal access token. If None, will try to load from environment.
        """
        load_dotenv()
        self.access_token = access_token or os.getenv('GITHUB_TOKEN')
        
        if not self.access_token:
            raise ValueError(
                "GitHub token not provided. Set GITHUB_TOKEN environment variable "
                "or pass it as an argument."
            )
        
        self.github = Github(self.access_token)
        self.user = self.github.get_user()
    
    def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = False,
        auto_init: bool = True,
        gitignore_template: Optional[str] = None,
        license_template: Optional[str] = None,
        has_issues: bool = True,
        has_wiki: bool = True,
        has_projects: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a new GitHub repository.
        
        Args:
            name: Repository name
            description: Repository description
            private: Whether the repository should be private
            auto_init: Initialize repository with a README
            gitignore_template: .gitignore template to use (e.g., 'Python', 'Node')
            license_template: License template to use (e.g., 'mit', 'apache-2.0')
            has_issues: Enable issues
            has_wiki: Enable wiki
            has_projects: Enable projects
            
        Returns:
            Dictionary with repository information
        """
        try:
            print(f"Creating repository '{name}'...")
            
            repo = self.user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=auto_init,
                gitignore_template=gitignore_template,
                license_template=license_template,
                has_issues=has_issues,
                has_wiki=has_wiki,
                has_projects=has_projects,
            )
            
            print(f"✓ Repository created successfully!")
            
            return {
                'name': repo.name,
                'full_name': repo.full_name,
                'html_url': repo.html_url,
                'clone_url': repo.clone_url,
                'ssh_url': repo.ssh_url,
                'private': repo.private,
                'description': repo.description,
            }
            
        except GithubException as e:
            print(f"✗ Error creating repository: {e.data.get('message', str(e))}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"✗ Unexpected error: {str(e)}", file=sys.stderr)
            raise
    
    def list_repositories(self, max_repos: int = 10):
        """
        List user's repositories.
        
        Args:
            max_repos: Maximum number of repositories to display
        """
        print(f"Listing repositories for {self.user.login}:")
        print("-" * 60)
        
        repos = self.user.get_repos()[:max_repos]
        
        if not repos:
            print("No repositories found.")
            return
        
        for i, repo in enumerate(repos, 1):
            visibility = "Private" if repo.private else "Public"
            print(f"{i}. {repo.name} ({visibility})")
            if repo.description:
                print(f"   Description: {repo.description}")
            print(f"   URL: {repo.html_url}")
            print()


def main():
    """Main function to run the repository creator from command line."""
    parser = argparse.ArgumentParser(
        description='Create GitHub repositories programmatically',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a public repository
  python create_repository.py my-new-repo --description "My awesome project"
  
  # Create a private repository with Python template
  python create_repository.py my-private-repo --private --gitignore Python
  
  # Create a repository with MIT license
  python create_repository.py my-licensed-repo --license mit
  
  # List existing repositories
  python create_repository.py --list
        """
    )
    
    parser.add_argument(
        'name',
        nargs='?',
        help='Repository name'
    )
    
    parser.add_argument(
        '--description',
        default='',
        help='Repository description'
    )
    
    parser.add_argument(
        '--private',
        action='store_true',
        help='Make repository private'
    )
    
    parser.add_argument(
        '--no-init',
        action='store_true',
        help='Do not initialize with README'
    )
    
    parser.add_argument(
        '--gitignore',
        help='Gitignore template (e.g., Python, Node, Java)'
    )
    
    parser.add_argument(
        '--license',
        help='License template (e.g., mit, apache-2.0, gpl-3.0)'
    )
    
    parser.add_argument(
        '--no-issues',
        action='store_true',
        help='Disable issues'
    )
    
    parser.add_argument(
        '--no-wiki',
        action='store_true',
        help='Disable wiki'
    )
    
    parser.add_argument(
        '--no-projects',
        action='store_true',
        help='Disable projects'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List existing repositories'
    )
    
    parser.add_argument(
        '--token',
        help='GitHub personal access token (or set GITHUB_TOKEN env var)'
    )
    
    args = parser.parse_args()
    
    try:
        creator = RepositoryCreator(access_token=args.token)
        
        if args.list:
            creator.list_repositories()
            return
        
        if not args.name:
            parser.error("Repository name is required (unless using --list)")
        
        result = creator.create_repository(
            name=args.name,
            description=args.description,
            private=args.private,
            auto_init=not args.no_init,
            gitignore_template=args.gitignore,
            license_template=args.license,
            has_issues=not args.no_issues,
            has_wiki=not args.no_wiki,
            has_projects=not args.no_projects,
        )
        
        print("\nRepository Details:")
        print(f"  Name: {result['name']}")
        print(f"  Full Name: {result['full_name']}")
        print(f"  URL: {result['html_url']}")
        print(f"  Clone URL: {result['clone_url']}")
        print(f"  SSH URL: {result['ssh_url']}")
        print(f"  Visibility: {'Private' if result['private'] else 'Public'}")
        
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except GithubException:
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
