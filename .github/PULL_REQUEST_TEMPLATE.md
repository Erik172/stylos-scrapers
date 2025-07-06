## 📋 Description

<!-- Provide a clear and concise description of the changes -->

### Type of Change
<!-- Mark the applicable change type with an 'x' -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 🕷️ New retailer/spider
- [ ] 🔧 Improvement/refactor (non-breaking change that neither fixes a bug nor adds a feature)
- [ ] 📚 Documentation (changes to documentation only)
- [ ] 🧪 Tests (adding missing tests or correcting existing tests)
- [ ] 🐳 Infrastructure (changes to Docker, CI/CD, configuration)

### Summary of Changes
<!-- Briefly describe what you have changed -->

### Main Files Modified
<!-- List the most important files that have been modified -->

- `stylos/spiders/` - 
- `stylos/extractors/` - 
- `tests/` - 
- Other: 

---

## 🧪 Testing

### Tests Performed
<!-- Check all the tests that you have run -->

- [ ] Unit tests: `pytest tests/`
- [ ] Manual spider test: `scrapy crawl [spider_name]`
- [ ] Test with specific URL: `python control_scraper.py --spider [name] --url [url]`
- [ ] Test in Docker: `docker-compose up -d && [test command]`
- [ ] Style check: `flake8 stylos/`

### Testing Results
<!-- Describe the results of your tests -->

```bash
# Example results
pytest tests/ -v
================================ test session starts ================================
platform darwin -- Python 3.11.5
collected 15 items

tests/test_new_extractor.py::test_extract_product_data PASSED       [ 80%]
tests/test_new_extractor.py::test_extract_menu_data PASSED          [100%]

================================ 15 passed in 2.34s =================================
```

### Test Data
<!-- If it's a new spider, include examples of extracted data -->

<details>
<summary>📊 Example of extracted data (click to expand)</summary>

```json
{
  "url": "https://example.com/product",
  "name": "EXAMPLE PRODUCT",
  "description": "product description",
  "current_price": 89900.0,
  "original_price": 129900.0,
  "currency": "COP",
  "has_discount": true,
  "discount_percentage": 30.79,
  "images_by_color": [
    {
      "color": "BLACK",
      "images": [
        {
          "src": "https://example.com/image1.jpg",
          "alt": "Black Product",
          "img_type": "product_image"
        }
      ]
    }
  ],
  "site": "NEW_RETAILER",
  "datetime": "2025-01-XX"
}
```

</details>

---

## 🔍 Quality Checklist

### Code
- [ ] The code follows PEP 8 conventions
- [ ] I have added docstrings to new/modified methods
- [ ] I have used type hints where appropriate
- [ ] The code handles errors appropriately (try/except)
- [ ] I have used logging instead of print()
- [ ] The CSS/XPath selectors are robust (not dependent on specific IDs)

### Spider/Extractor (if applicable)
- [ ] The spider respects robots.txt and terms of service
- [ ] It implements appropriate rate limiting
- [ ] It gracefully handles timeouts and network errors
- [ ] It only extracts public and necessary data
- [ ] Images are correctly organized by color
- [ ] Prices are extracted in the correct currency

### Testing
- [ ] I have added unit tests for new code
- [ ] Tests cover success and error cases
- [ ] I have tested the code manually
- [ ] Tests pass in local and Docker mode
- [ ] I have verified that I am not breaking existing functionality

### Documentation
- [ ] I have updated RETAILERS.md (if it's a new retailer)
- [ ] I have added comments for complex logic
- [ ] I have documented any new configuration
- [ ] I have updated usage examples if necessary

---

## 🌍 Impact and Considerations

### Compatibility
- [ ] The changes are backwards compatible
- [ ] They do not affect existing spiders
- [ ] It works with the current Docker configuration
- [ ] It is compatible with supported Python versions (3.11+)

### Performance
- [ ] The changes do not negatively affect performance
- [ ] I have considered the memory usage of the new code
- [ ] I have optimized selectors to be efficient
- [ ] I have considered the impact on the target server

### Ethics and Compliance
- [ ] I respect the retailer's terms of service
- [ ] I only extract public and necessary data
- [ ] I have implemented appropriate rate limiting
- [ ] The user agent is transparent about its purpose

---

## 📸 Screenshots (if applicable)

<!-- If there are visual changes or new features, add screenshots -->

---

## 🔗 Related Issues

<!-- Mention any issue that this PR resolves -->
Closes #(issue_number)
Related to #(issue_number)

---

## 📝 Additional Notes

<!-- Any additional information that reviewers should know -->

### Design Decisions
<!-- Explain important decisions you made -->

### Known Limitations
<!-- If there are known limitations, document them -->

### Next Steps
<!-- If this PR is part of a larger work -->

---

## 🤝 Reviewer Checklist

<!-- For reviewer's use -->
- [ ] The code is clear and well-documented
- [ ] The tests are adequate and pass
- [ ] The changes meet the project's standards
- [ ] The functionality works as described
- [ ] There are no security or ethical issues
- [ ] The documentation is up-to-date

---

**Ready for review?** 🚀

Make sure you have completed all the checklist items before marking as "Ready for Review".