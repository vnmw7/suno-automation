# Development Guidelines

## Feature Implementation Philosophy
When implementing new features, always follow the **Minimum Viable Approach (MVA)**:

### Core Principles
1. **Start Simple**: Build the simplest working version first
2. **Avoid Over-Engineering**: Don't add complexity until proven necessary
3. **Single Responsibility**: Each function/component should do one thing well
4. **YAGNI (You Aren't Gonna Need It)**: Don't add functionality until actually needed

### Implementation Steps
1. **Define the Core Requirement**: What is the absolute minimum needed?
2. **Build the MVP**: Implement only essential functionality
3. **Test Basic Flow**: Ensure the happy path works
4. **Iterate if Needed**: Add complexity only when requirements demand it

### Planning and Review Requirement
When creating an implementation plan, always include the exact file path(s) relative to the project root and file name(s) that will be changed, and paste the current code snippet(s) from those files that will be affected. This ensures reviewers can see the precise location and the existing code context during review. Keep snippets minimal (just the relevant function/class/block) and clearly annotate which lines or regions will change.

### Code Guidelines
- Prefer simple functions over complex classes
- Use built-in libraries before adding dependencies
- Write straightforward, readable code over clever solutions
- Avoid premature optimization
- Keep error handling simple but effective
- When defining UI selectors, rely on stable attributes (aria-label, role, deterministic text) and avoid dynamic or hashed identifiers unless unavoidable.

### File Header Requirements
Every source file must include a header at the beginning containing:
- **System name**: Project or System name here
- **Module name**: (if applicable)
- **File URL**: Relative Path to the file
- **Purpose**: Brief description of the file's purpose

Example:
```python
"""
System: {Project/System Name}
Module: Song Download
File URL: project-root/filename.example
Purpose: Download and process songs from {Project/System Name} API with error handling
"""
```

### Example Approach
```python
# ❌ Over-engineered
class ComplexFeatureManager:
    def __init__(self, config, logger, cache, ...):
        # 50 lines of setup
    
    def execute_with_retry_and_cache(self, ...):
        # Complex logic with multiple layers

# ✅ Minimalistic
def simple_feature(input_data):
    # Direct, clear implementation
    result = process_data(input_data)
    return result
```

### Testing Commands
Run these commands after implementing features:
- Linting: `npm run lint` (if applicable)
- Type checking: `npm run typecheck` (if applicable)
- Python linting: `ruff check` (if applicable)

## Identifiers (Variables, Constants, and Macros)

### Variables

Variable names must contain alphanumeric characters only.

All other variable names should be of mixed case and begin with a lowercase.

If an acronym is contained in a name, it should not be used in all uppercase form, e.g., use `strHtmlContent` and NOT `strHTMLContent`.

Abbreviations and acronyms must be avoided. However, if names are getting longer, vowels may be eliminated, e.g., `chrFirstElmnt`, or use an unambiguous prefix, e.g., `chrFirstElem` but NOT `fE`.

Commonly abbreviated variables may be applied but only abbreviations which are on the list Table Variable Context Prefix can be used for consistency.

The names of all variables should be prepended with the following prefixes enumerated below to clearly describe the contents, scope, and type of the variable.

| Data Type   | Prefix | Example     |
| :---------- | :----- | :---------- |
| Byte        | byt    | bytMaterial |
| Integer     | int    | intAge      |
| Long        | lng    | lngValue    |
| Float       | flt    | fltInterest |
| Double      | dbl    | dblPage     |
| Currency    | cur    | curSalary   |
| Character   | chr    | chrCode     |
| String      | str    | strFile     |
| Text        | txt    | txtParagraph |
| Date        | dt     | dttBirthday |
| Time        | tm     | tmStart     |
| Date/Time   | dtm    | dtmMeeting  |
| Boolean     | bln    | blnActive   |
| Array       | arr    | arrMonths   |
| Object      | obj    | objEmployee |
| Error       | err    | errEntry    |
| User defined type | udt    | udtReturnValue |

Variable Type Prefix

| Scope     | Prefix | Example     |
| :-------- | :----- | :---------- |
| Global    | g_     | g_intCounter |
| Local     | None   | blnStatus   |
| Public    | pub_   | pub_objAll  |
| Protected | prt_   | prt_objClass |
| Private   | prv_   | prv_objMember |

Variable Scope Prefix

| Usage     | Prefix |
| :-------- | :----- |
| Array     | arr    |
| Average   | avg    |
| Column    | col    |
| Command   | cmd    |
| Control   | ctl    |
| Counter   | ctr    |
| Data      | dat    |
| Day       | da     |
| Degrees   | deg    |
| Dialog    | dlg    |
| File      | fil    |
| Flag      | flg    |
| Form      | frm    |
| Function  | fnc    |
| Graph     | gph    |
| High      | hi     |
| Hour      | hr     |
| Image     | img    |
| Index     | idx    |
| Key       | key    |
| Label     | lbl    |
| Length    | len    |
| Low       | lo     |
| Maximum   | max    |
| Menu      | mnu    |
| Message   | msg    |
| Minimum   | min    |
| Minute    | mi     |
| Month     | mo     |
| Number    | num    |
| Object    | obj    |
| Picture   | pic    |
| Pointer   | ptr    |
| Register  | reg    |
| Report    | rpt    |
| Second    | sc     |
| State     | sta    |
| Timer     | tmr    |
| Void      | vd     |
| Week      | wk     |
| Window    | win    |
| Year      | yr     |

Variable Context Prefix

Array element names follow the same rules as a variable. Access an array's elements with single quotes, e.g., `$arrValue = $array('intElement')`.

For consistency, a variable name may take the name of a passing identifier regardless of style.

### Constants and Macros

Use constants and macros instead of hard coded literal values. If supported by the language, literal values shall be avoided in code statements; rather, a symbolic constant for each shall be defined reflecting its intent. 0 should not be assumed to mean "OFF", a symbolic constant OFF should be defined to be equal to 0. The numeric literals 0 and 1 shall not be used as Boolean constants. Booleans are not to be treated as integers.

Constants and macros shall not be defined in more than one textual location in the program, even if the multiple definitions are exactly the same.

The names of constants should be in all uppercase form. Use underscore "_" to separate words.

## File and Module Standards

### Modularization
- All source code will be grouped into modules having one source code file to contain the implementation of one module.
- Each module will deal with a single, unique domain. The use of information hiding is mandatory, to the extent allowed by the given language. The code that deals with a given domain shall protect, to the greatest extent possible in the given language, its data, its data structure design, and its internal operations on the data.
- Emphasize simplicity, clarity, cohesion, and decoupling in decomposing a specific system into constituent modules.
- Minimize scope of variables whenever allowed by the language. All constants, types, and variables shall be declared only within the scope in which they need to be known.
- Aim to achieve a low coupling, high cohesion, and clean interfaces final product. It is not easy to attain all at the same time but the modularization of the program will be cleaner and easier to maintain.
## File Directory Structure

### Framework Directory Guidelines
- Use a framework and strictly follow the directory structure of the framework being applied
- Place coding resources like scripts and style sheets under a folder named "assets"
- Classify resources into sub-folders within assets
- Place the "assets" folder outside of the framework directory structure
- Additional folders may be created in the base directory only if needed
- A subfolder may be added provided that its content matches with the description of its parent folder
  - Example: Third-party folder may contain subfolders for specific package libraries
- **Limit folder depth**: Construct no more than 3 levels of folders as much as possible

### Example Structure
```
project/
├── assets/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── fonts/
├── src/           # Framework directory
├── config/
└── vendor/        # Third-party packages
```

## Function, Method and Class Naming Conventions

### General Rules
- Names should only contain alphabetic characters (no numbers, spaces, or underscores)
- **Class names**: Start with uppercase (PascalCase)
- **Method/Function names**: Start with lowercase (camelCase)
- Acronyms should not be all uppercase
  - ✅ Correct: `getHtmlPage()`
  - ❌ Wrong: `getHTMLPage()`

### Descriptive Naming
- Use names that describe the role/purpose
  - ✅ `computeTotal()` instead of ❌ `Total()`
- Action methods should clearly state what they do
  - ✅ `checkForErrors()` instead of ❌ `errorCheck()`
  - ✅ `importToTable()` instead of ❌ `importTable()`

### Boolean Functions
- Should be in question form and positive sense
  - ✅ `isEnabled()`
  - ❌ `isNotEnabled()`

### Naming Prefixes
- **is** - Returns boolean values (`isNull()`, `isEmpty()`)
- **get** - Retrieves a value (`getPassword()`, `getUserName()`)
- **set** - Sets a value (`setPassword()`, `setUserName()`)
- **has** - Checks existence (`hasPermission()`, `hasAccess()`)
- **can** - Checks capability (`canEdit()`, `canDelete()`)

### Naming Suffixes
- **Max** - Maximum value (`findMax()`, `getAgeMax()`)
- **Min** - Minimum value (`findMin()`, `getPriceMin()`)
- **Cnt** - Count variable (`getRecordCnt()`, `getUserCnt()`)
- **Key** - Key value (`getPrimaryKey()`, `getForeignKey()`)

### Access Modifiers
- Private/Protected methods must start with underscore
  - Private: `_calculateInternal()`
  - Protected: `_setMonth()`
  - Public: `getMonth()`

### Examples
```python
class UserManager:  # Class - PascalCase
    def getUserById(self, userId):  # Public method - camelCase
        pass

    def _validateUser(self, user):  # Private method - underscore prefix
        pass

    def isActive(self):  # Boolean method - question form
        pass

    def getRecordCnt(self):  # Using suffix for count
        pass
```

## API Version Control Standards

### URL Versioning Strategy
- **Always** implement version control in API endpoints using URL path versioning
- **Format**: `{backend_url}/api/v{major_version}/{resource}`
- **Example**: `http://localhost:8000/api/v1/songs`, `http://localhost:8000/api/v2/users`

### Version Implementation Guidelines
1. **Major Version Changes (v1 → v2)**:
   - Breaking changes to response structure
   - Removal of existing endpoints
   - Changes to authentication methods
   - Incompatible data format changes

2. **Minor Updates**: Handle through backward-compatible changes within same major version
   - Adding new optional fields
   - Adding new endpoints
   - Performance improvements

3. **Version Support Policy**:
   - Maintain at least 2 major versions simultaneously
   - Provide deprecation notices 3-6 months before removing old versions
   - Document migration path from old to new versions

### Implementation Example
```python
# Flask/FastAPI example
@app.route('/api/v1/songs', methods=['GET'])  # Current stable
@app.route('/api/v2/songs', methods=['GET'])  # Next version with new features

# Include version in response headers
response.headers['API-Version'] = 'v1'
response.headers['Deprecation'] = 'true'  # If applicable
response.headers['Sunset'] = '2025-12-31'  # Deprecation date
```
