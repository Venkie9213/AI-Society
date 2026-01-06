#!/usr/bin/env python3
"""
Example: Batch Repository Creation
This example demonstrates how to create multiple repositories programmatically.
"""

from create_repository import RepositoryCreator
import time


def create_multiple_repositories():
    """Create multiple repositories with different configurations."""
    
    # Initialize the creator
    creator = RepositoryCreator()
    
    # Define repositories to create
    repositories = [
        {
            'name': 'ml-experiments',
            'description': 'Machine Learning experiments and notebooks',
            'private': False,
            'gitignore_template': 'Python',
            'license_template': 'mit',
        },
        {
            'name': 'web-dashboard',
            'description': 'Interactive web dashboard for data visualization',
            'private': False,
            'gitignore_template': 'Node',
            'license_template': 'mit',
        },
        {
            'name': 'personal-notes',
            'description': 'Private notes and documentation',
            'private': True,
            'gitignore_template': None,
            'license_template': None,
        },
    ]
    
    print(f"Creating {len(repositories)} repositories...\n")
    
    created_repos = []
    failed_repos = []
    
    for repo_config in repositories:
        try:
            result = creator.create_repository(**repo_config)
            created_repos.append(result)
            print(f"✓ Created: {result['html_url']}\n")
            
            # Be nice to the API - add a small delay between creations
            time.sleep(1)
            
        except Exception as e:
            failed_repos.append({
                'name': repo_config['name'],
                'error': str(e)
            })
            print(f"✗ Failed to create {repo_config['name']}: {e}\n")
    
    # Summary
    print("=" * 60)
    print(f"Summary: {len(created_repos)} created, {len(failed_repos)} failed")
    print("=" * 60)
    
    if created_repos:
        print("\nSuccessfully Created:")
        for repo in created_repos:
            print(f"  - {repo['full_name']}: {repo['html_url']}")
    
    if failed_repos:
        print("\nFailed:")
        for repo in failed_repos:
            print(f"  - {repo['name']}: {repo['error']}")


def create_repository_with_custom_settings():
    """Create a repository with custom settings."""
    
    creator = RepositoryCreator()
    
    # Create a repository with all custom settings
    result = creator.create_repository(
        name='advanced-ai-project',
        description='Advanced AI project with custom configuration',
        private=False,
        auto_init=True,
        gitignore_template='Python',
        license_template='apache-2.0',
        has_issues=True,
        has_wiki=True,
        has_projects=True,
    )
    
    print("\nRepository created with custom settings:")
    print(f"  URL: {result['html_url']}")
    print(f"  Clone: {result['clone_url']}")


if __name__ == '__main__':
    print("Repository Creation Examples")
    print("=" * 60)
    print("\nChoose an example to run:")
    print("1. Create multiple repositories")
    print("2. Create repository with custom settings")
    print("\nNote: This will create actual repositories in your GitHub account!")
    print("Comment out the examples you don't want to run.\n")
    
    # Uncomment the example you want to run:
    
    # Example 1: Create multiple repositories
    # create_multiple_repositories()
    
    # Example 2: Create repository with custom settings
    # create_repository_with_custom_settings()
    
    print("\nTo run an example, uncomment the desired function call in this file.")
