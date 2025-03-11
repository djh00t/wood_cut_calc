# Wood Cut Calculator - Guidelines for Claude

## Commands

- **Run**: `flask run` or `python app.py`
- **Init Database**: `flask initdb`
- **Debug Mode**: App runs in debug mode by default
- **Testing**: No testing framework currently implemented

## Code Style

- **Imports**: Standard library first, followed by third-party (e.g., Flask), then local modules
- **Formatting**: 4-space indentation, 79-character line limit
- **Naming**:
  - Functions/variables: snake_case
  - Constants: UPPER_CASE
  - Classes: PascalCase
- **Documentation**: Docstrings for functions (see calculate_cutting_plan and template filters)
- **Error Handling**: Currently using Flask's flash messages for user feedback
- **Google Style Guide**: <https://google.github.io/styleguide/pyguide.html>
- **PEP 8**: <https://pep8.org/>
- **Conventional Commits**: <https://www.conventionalcommits.org/en/v1.0.0/>
  - **You must include**: a type, scope, and message in your commit message
  - **Types**: feat, fix, docs, style, refactor, perf, test, chore, ci, build,
    revert, wip, security, release, deploy, infra, init, ui
  - **Scopes**: Use the most specific of the following, in this order of preference:
    1. **File Name** – When the change affects an entire file or module.
        - ***Example***: feat(app.py): add logging to user authentication
        - ***Use when***: The change applies broadly to the file (e.g., restructuring, new imports, or refactoring across functions).
    2. **Class Name** – When modifying a specific class within a file.
        - ***Example***: fix(CuttingPlan): correct offcut calculation
        - ***Use when***: The change is isolated to a single class and does not affect other classes in the same file.
    3. **Function Name** – When a specific function is changed.
        - ***Example***: refactor(calculate_cutting_plan): simplify loop structure
        - ***Use when***: The change is contained within a function/method and does not alter class-level behavior.
    4. **Variable Name** – When modifying a specific variable, especially if it’s a
       global, module-level, or significant within a function.
        - ***Example***: style(inventory): rename for clarity
        - ***Use when***: The change impacts a variable, improving readability or refactoring its usage.

    **Multiple Scopes?**

    - If more than one scope applies, use the most specific (e.g., prefer Function Name over File Name if the change is isolated).
    - If multiple classes or functions are affected, use the common parent file instead.
    - ***Example***: fix(order_processing): correct tax calculation in apply_discount and finalize_order

    **Cross-cutting Changes?**

    - Use a broader module or feature name if a single scope isn’t clear.
    - ***Example***: chore(logging): standardize log levels across modules
  
- **Test Driven Development**: Break the project into sets of deliverables and write tests for each deliverable before writing code. This will help you focus on the requirements and ensure that your code is working as expected.

## Architecture

- Flask web application with SQLite database
- Templates use Jinja2 with custom filters in custom_filters.py
- Database access via helper functions (query_db, modify_db)
- Core cutting algorithm in calculate_cutting_plan function
- RESTful routing pattern for resources (suppliers, inventory, projects, cuts)
- Use semver for versioning (e.g., v1.0.0)
- Use automatic release notes generation from conventional commits (e.g., GitHub Actions)
- Package in Docker container for deployment
- Publish Docker image to GitHub Container Registry and Dockerhub
- Use environment variables for configuration
- Implement logging for debugging
- Implement testing framework (pytest)
- Implement CI/CD pipeline (GitHub Actions)

## Database Migrations

When making database schema changes:
1. Always export existing data before applying schema changes
2. Apply schema modifications (ALTER TABLE, CREATE TABLE, etc.)
3. Re-import the data with proper mapping to the new fields
4. Verify data integrity after migration is complete

This ensures no user data is lost during schema evolution.

When working on this project, maintain the existing patterns and document any complex algorithms with detailed comments.
