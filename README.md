# AI-Society: Autonomous Repository Creation

This project demonstrates the ability to create GitHub repositories programmatically and autonomously. It provides a Python-based tool that can create repositories with various configurations using the GitHub API.

## Features

- ✨ Create GitHub repositories programmatically
- 🔧 Configure repository settings (visibility, issues, wiki, projects)
- 📝 Initialize with README, .gitignore, and license templates
- 🎯 Command-line interface for easy usage
- 📦 Batch creation of multiple repositories
- 🔍 List existing repositories

## Prerequisites

- Python 3.7 or higher
- A GitHub account
- A GitHub Personal Access Token with `repo` scope

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Venkie9213/AI-Society.git
cd AI-Society
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure GitHub Token

Create a GitHub Personal Access Token:
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name
4. Select the `repo` scope (Full control of private repositories)
5. Click "Generate token"
6. Copy the token

Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your token:
```
GITHUB_TOKEN=your_actual_token_here
```

Alternatively, export it as an environment variable:
```bash
export GITHUB_TOKEN=your_actual_token_here
```

## Usage

### Basic Usage

Create a simple public repository:
```bash
python create_repository.py my-new-repo --description "My awesome project"
```

### Advanced Usage

Create a private repository with Python .gitignore:
```bash
python create_repository.py my-private-repo --private --gitignore Python --description "Private Python project"
```

Create a repository with MIT license:
```bash
python create_repository.py my-licensed-repo --license mit --description "Licensed project"
```

Create a repository with all options:
```bash
python create_repository.py advanced-project \
    --description "Advanced project with custom settings" \
    --private \
    --gitignore Python \
    --license apache-2.0 \
    --no-wiki
```

List your existing repositories:
```bash
python create_repository.py --list
```

### Command-Line Options

```
positional arguments:
  name                  Repository name

optional arguments:
  -h, --help            Show help message
  --description DESC    Repository description
  --private             Make repository private (default: public)
  --no-init             Do not initialize with README
  --gitignore TEMPLATE  Gitignore template (e.g., Python, Node, Java)
  --license LICENSE     License template (e.g., mit, apache-2.0, gpl-3.0)
  --no-issues           Disable issues
  --no-wiki             Disable wiki
  --no-projects         Disable projects
  --list                List existing repositories
  --token TOKEN         GitHub personal access token
```

### Programmatic Usage

You can also use the `RepositoryCreator` class in your own Python scripts:

```python
from create_repository import RepositoryCreator

# Initialize with token (or use environment variable)
creator = RepositoryCreator()

# Create a repository
result = creator.create_repository(
    name='my-new-repo',
    description='Created programmatically',
    private=False,
    gitignore_template='Python',
    license_template='mit'
)

print(f"Repository created: {result['html_url']}")
```

### Batch Creation

See `examples.py` for more advanced usage patterns, including batch creation of multiple repositories.

## Available Templates

### .gitignore Templates
Common templates include: `Python`, `Node`, `Java`, `Go`, `Ruby`, `C++`, `C`, `Swift`, `Kotlin`, and many more.

### License Templates
Common licenses include:
- `mit` - MIT License
- `apache-2.0` - Apache License 2.0
- `gpl-3.0` - GNU General Public License v3.0
- `bsd-3-clause` - BSD 3-Clause License
- `agpl-3.0` - GNU Affero General Public License v3.0
- `unlicense` - The Unlicense

For a complete list, see [GitHub's license API](https://docs.github.com/en/rest/licenses).

## Examples

### Example 1: Create a Machine Learning Project Repository

```bash
python create_repository.py ml-experiments \
    --description "Machine Learning experiments and notebooks" \
    --gitignore Python \
    --license mit
```

### Example 2: Create a Private Web Project

```bash
python create_repository.py web-dashboard \
    --description "Interactive web dashboard" \
    --private \
    --gitignore Node \
    --license apache-2.0
```

### Example 3: Batch Creation

Run the examples script to create multiple repositories at once:

```bash
python examples.py
```

Edit `examples.py` to customize the repositories you want to create.

## Error Handling

The tool includes comprehensive error handling:
- **Authentication errors**: Verify your GitHub token is valid
- **Name conflicts**: Repository name already exists
- **Rate limiting**: GitHub API rate limits apply
- **Permission errors**: Ensure token has `repo` scope

## Security Notes

⚠️ **Important**: Never commit your `.env` file or expose your GitHub token. The `.gitignore` file is configured to exclude `.env` files.

## Can AI Create Repositories by Itself?

**Yes!** This project demonstrates that AI and automation tools can:

1. **Create repositories programmatically** using the GitHub API
2. **Configure repository settings** including visibility, features, and templates
3. **Batch create multiple repositories** with different configurations
4. **Integrate with CI/CD pipelines** for automated project initialization
5. **Provide self-service repository creation** for teams and organizations

This capability enables:
- **Automated project scaffolding** for new initiatives
- **Template-based repository creation** for consistent project structures
- **Self-service workflows** where AI agents can create and manage repositories
- **Integration with AI coding assistants** for complete project setup

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Built with [PyGithub](https://github.com/PyGithub/PyGithub)
- Powered by the [GitHub REST API](https://docs.github.com/en/rest)

## Support

For issues or questions:
1. Check the [GitHub API documentation](https://docs.github.com/en/rest)
2. Review the error messages for specific guidance
3. Ensure your GitHub token has the correct permissions
4. Open an issue in this repository

---

**Answer to "Can you create repositories by yourself?"**

**Absolutely yes!** This project proves that repositories can be created programmatically and autonomously using the GitHub API. Whether through command-line tools, Python scripts, or integrated into larger automation workflows, repository creation can be fully automated without manual GitHub UI interaction.
