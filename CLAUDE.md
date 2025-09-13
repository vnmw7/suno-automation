# Development Guidelines

## Song File Naming Convention
When downloading or processing songs, ALWAYS use the song_id format for filenames:
- **Expected format**: `{slug_title}_{song_id}_{timestamp}.mp3`
- **Example**: `isaiah-1-1-10_0536dd17-8cfd-4bca-9fd7-831621daac10_20250913152839.mp3`
- **DO NOT** use index values in filenames (no `_index_` pattern)
- All song references and fetching should expect this song_id-based naming pattern

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

### Code Guidelines
- Prefer simple functions over complex classes
- Use built-in libraries before adding dependencies
- Write straightforward, readable code over clever solutions
- Avoid premature optimization
- Keep error handling simple but effective

### File Header Requirements
Every source file must include a header at the beginning containing:
- **System name**: Suno Automation
- **Module name**: (if applicable)
- **Purpose**: Brief description of the file's purpose

Example:
```python
"""
System: Suno Automation
Module: Song Download
Purpose: Download and process songs from Suno API with error handling
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
- remember to implement version control in backend apis like {backendurl}/api/v1/