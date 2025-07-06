# 📋 GitHub Templates - Stylos Scrapers

This folder contains all the templates and configurations needed to maintain an organized and professional open-source project.

## 🎯 Available Templates

### 🐛 Reporting Bugs

#### 🕷️ Spider Bug (`bug-spider.yml`)
For reporting specific issues with data extraction from spiders:
- CSS/XPath selectors not working
- Incorrect price extraction
- Problems with images or navigation
- Selenium TimeoutException

**Use this template when:**
- A spider is not extracting data correctly
- Selectors have stopped working
- There are specific issues with a retailer

#### 🐳 Infrastructure Bug (`bug-infrastructure.yml`)
For issues related to Docker, Selenium Grid, memory, etc.:
- Restarting containers
- Memory or CPU problems
- Connectivity errors
- Docker Compose configuration

**Use this template when:**
- Docker is not working correctly
- Selenium Grid has issues
- There are performance or memory issues

### ✨ Requesting Features

#### 🆕 Feature Request (`feature-request.yml`)
For requesting new features or improvements:
- New retailers/spiders
- Improvements to existing extractors
- New API functionalities
- Performance optimizations

**Use this template when:**
- You want a new retailer to be supported
- You have ideas to improve the project
- You need additional functionality

### ❓ Help and Questions

#### 🤝 Question / Help (`question.yml`)
For asking general questions or requesting help:
- Initial setup
- Using existing spiders
- General troubleshooting
- Web scraping concepts

**Use this template when:**
- You need help setting up the project
- You don't understand how to use something
- You have general technical questions

## 📝 Pull Requests

### 🔄 PR Template (`PULL_REQUEST_TEMPLATE.md`)
A complete template for Pull Requests that includes:
- Description of the change
- Testing checklist
- Code quality checklist
- Ethical considerations
- Sample data

**Main sections:**
- **Description**: What changes were made
- **Testing**: What tests were executed
- **Quality Checklist**: Code verifications
- **Impact**: Compatibility considerations
- **Screenshots**: For visual changes

## ⚙️ Configuration

### 📋 Config.yml (`config.yml`)
Template configuration that:
- Disables blank issues
- Provides useful links
- Directs to relevant documentation

**Included links:**
- Main documentation (README.md)
- Contribution guide (CONTRIBUTING.md)
- Retailer status (RETAILERS.md)
- GitHub Discussions
- Direct contact

## 🎨 Template Features

### ✅ **Structured Fields**
- Dropdowns for categorization
- Required and optional fields
- Automatic validation
- Appropriate code rendering

### 🏷️ **Automatic Labels**
- `bug` + `spider` for spider bugs
- `bug` + `infrastructure` for infra bugs
- `enhancement` for feature requests
- `question` for questions

### 📋 **Interactive Checklists**
- Documentation verification
- Troubleshooting steps
- Quality criteria
- Pre-submission validations

### 🎯 **Web Scraping Specifics**
- Fields for example URLs
- Sections for CSS selectors
- Retailer information
- Ethical considerations

## 🚀 Recommended Usage

### For Contributors
1.  **Before reporting a bug**: Review the documentation
2.  **Spider bugs**: Include a specific URL and logs
3.  **Infra bugs**: Include Docker configuration
4.  **Feature requests**: Provide clear use cases
5.  **Pull requests**: Complete all checklists

### For Maintainers
1.  **Triaging**: Automatic labels help categorize issues
2.  **Complete information**: Templates ensure necessary info is provided
3.  **Quality**: Checklists improve the quality of PRs
4.  **Consistency**: Standard format for all reports

## 📚 Additional Resources

- **CONTRIBUTING.md**: Complete contribution guide
- **README.md**: Main project documentation
- **RETAILERS.md**: Current status of supported retailers
- **CODE_OF_CONDUCT.md**: Project's code of conduct

---

## 🛠️ Maintenance

These templates should be updated when:
- New retailers are added
- The project architecture changes
- Missing fields are identified in reports
- Tools or technologies are updated

To modify a template:
1.  Edit the corresponding `.yml` file
2.  Test the template by creating a test issue
3.  Update this documentation if necessary

---

**Goal**: To facilitate quality contributions and keep the project organized 🎯