"""
Phase 1 Test Fixtures

Mock HTML pages for testing the accessibility parser.
"""

__version__ = "1.0.0"

# ============================================================================
# SIMPLE LOGIN FORM
# ============================================================================

SIMPLE_LOGIN_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Login Form</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 400px;
            margin: 50px auto;
            padding: 20px;
        }
        form {
            border: 1px solid #ccc;
            padding: 20px;
            border-radius: 5px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 3px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 10px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <h1>Login</h1>
    <form id="login-form">
        <div class="form-group">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" placeholder="Enter your username" required>
        </div>
        
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" placeholder="Enter your password" required>
        </div>
        
        <button type="submit" id="submit-button">Sign In</button>
    </form>
</body>
</html>
"""

# ============================================================================
# COMPLEX FORM (Multiple Input Types)
# ============================================================================

COMPLEX_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complex Form</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input,
        textarea,
        select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 3px;
            box-sizing: border-box;
            font-family: Arial, sans-serif;
        }
        .checkbox-group,
        .radio-group {
            margin-top: 10px;
        }
        .checkbox-item,
        .radio-item {
            margin-bottom: 8px;
        }
        button {
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background-color: #0056b3;
        }
        .hidden-element {
            display: none;
        }
    </style>
</head>
<body>
    <h1>Comprehensive Form</h1>
    <form id="complex-form">
        <!-- Text Input -->
        <div class="form-group">
            <label for="fullname">Full Name</label>
            <input type="text" id="fullname" name="fullname" placeholder="Enter full name" required>
        </div>
        
        <!-- Email Input -->
        <div class="form-group">
            <label for="email">Email Address</label>
            <input type="email" id="email" name="email" placeholder="Enter email" required>
        </div>
        
        <!-- Password Input -->
        <div class="form-group">
            <label for="pass">Password</label>
            <input type="password" id="pass" name="pass" placeholder="Enter password" required>
        </div>
        
        <!-- Textarea -->
        <div class="form-group">
            <label for="comments">Comments</label>
            <textarea id="comments" name="comments" rows="4" placeholder="Enter your comments"></textarea>
        </div>
        
        <!-- Select Dropdown -->
        <div class="form-group">
            <label for="country">Country</label>
            <select id="country" name="country" required>
                <option value="">-- Select a country --</option>
                <option value="usa">United States</option>
                <option value="uk">United Kingdom</option>
                <option value="canada">Canada</option>
            </select>
        </div>
        
        <!-- Checkboxes -->
        <div class="form-group">
            <label>Interests</label>
            <div class="checkbox-group">
                <div class="checkbox-item">
                    <input type="checkbox" id="sports" name="interests" value="sports">
                    <label for="sports">Sports</label>
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" id="music" name="interests" value="music">
                    <label for="music">Music</label>
                </div>
                <div class="checkbox-item">
                    <input type="checkbox" id="reading" name="interests" value="reading">
                    <label for="reading">Reading</label>
                </div>
            </div>
        </div>
        
        <!-- Radio Buttons -->
        <div class="form-group">
            <label>Gender</label>
            <div class="radio-group">
                <div class="radio-item">
                    <input type="radio" id="male" name="gender" value="male">
                    <label for="male">Male</label>
                </div>
                <div class="radio-item">
                    <input type="radio" id="female" name="gender" value="female">
                    <label for="female">Female</label>
                </div>
                <div class="radio-item">
                    <input type="radio" id="other" name="gender" value="other">
                    <label for="other">Other</label>
                </div>
            </div>
        </div>
        
        <!-- Buttons -->
        <div class="form-group">
            <button type="submit" id="submit-btn">Submit</button>
            <button type="reset" id="reset-btn">Reset</button>
        </div>
    </form>
    
    <!-- Hidden Element (should NOT be discovered) -->
    <div class="hidden-element">
        <button id="hidden-button">Hidden Button</button>
    </div>
</body>
</html>
"""

# ============================================================================
# PAGE WITH HIDDEN & ARIA-HIDDEN ELEMENTS
# ============================================================================

HIDDEN_ELEMENTS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hidden Elements Test</title>
</head>
<body>
    <h1>Visible and Hidden Elements</h1>
    
    <!-- Visible Buttons -->
    <button id="button1">Button 1 - Visible</button>
    <button id="button2">Button 2 - Visible</button>
    
    <!-- Hidden Button (CSS) -->
    <button id="button3" style="display: none;">Button 3 - Hidden with CSS</button>
    
    <!-- ARIA Hidden Button -->
    <button id="button4" aria-hidden="true">Button 4 - ARIA Hidden</button>
    
    <!-- Disabled Button -->
    <button id="button5" disabled>Button 5 - Disabled</button>
    
    <!-- Visibility Hidden -->
    <button id="button6" style="visibility: hidden;">Button 6 - Visibility Hidden</button>
</body>
</html>
"""

# ============================================================================
# NAVIGATION & LINKS PAGE
# ============================================================================

NAVIGATION_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Navigation Page</title>
    <style>
        nav {
            background-color: #333;
            padding: 10px;
            margin-bottom: 20px;
        }
        nav a {
            color: white;
            text-decoration: none;
            margin-right: 15px;
            padding: 5px 10px;
        }
        nav a:hover {
            background-color: #555;
        }
        .content {
            padding: 20px;
        }
    </style>
</head>
<body>
    <nav role="navigation" aria-label="Main navigation">
        <a href="#home" id="nav-home">Home</a>
        <a href="#about" id="nav-about">About</a>
        <a href="#services" id="nav-services">Services</a>
        <a href="#contact" id="nav-contact">Contact</a>
    </nav>
    
    <div class="content">
        <h1>Welcome</h1>
        <p>This is a navigation test page.</p>
        
        <h2>Related Links</h2>
        <ul>
            <li><a href="/page1" id="link1">Page 1</a></li>
            <li><a href="/page2" id="link2">Page 2</a></li>
            <li><a href="/page3" id="link3">Page 3</a></li>
        </ul>
    </div>
</body>
</html>
"""

# ============================================================================
# COMPLEX INTERACTIVE PAGE
# ============================================================================

COMPLEX_INTERACTIVE_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complex Interactive Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .header {
            border-bottom: 2px solid #333;
            margin-bottom: 20px;
        }
        .tabs {
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-bottom: 20px;
        }
        .tab-button {
            padding: 10px 20px;
            background: none;
            border: none;
            border-bottom: 3px solid transparent;
            cursor: pointer;
            font-size: 16px;
        }
        .tab-button.active {
            border-bottom-color: #007bff;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Interactive Components</h1>
    </div>
    
    <!-- Tabs -->
    <div class="tabs">
        <button class="tab-button active" id="tab1">Tab 1</button>
        <button class="tab-button" id="tab2">Tab 2</button>
        <button class="tab-button" id="tab3">Tab 3</button>
    </div>
    
    <div id="content1" class="tab-content active">
        <h2>Tab 1 Content</h2>
        <input type="text" id="input1" placeholder="Input in Tab 1">
        <button id="btn1">Action 1</button>
    </div>
    
    <div id="content2" class="tab-content">
        <h2>Tab 2 Content</h2>
        <input type="text" id="input2" placeholder="Input in Tab 2">
        <button id="btn2">Action 2</button>
    </div>
    
    <div id="content3" class="tab-content">
        <h2>Tab 3 Content</h2>
        <input type="text" id="input3" placeholder="Input in Tab 3">
        <button id="btn3">Action 3</button>
    </div>
    
    <!-- Dropdown -->
    <div style="margin-top: 30px;">
        <label for="options">Select Option:</label>
        <select id="options">
            <option>Option A</option>
            <option>Option B</option>
            <option>Option C</option>
        </select>
    </div>
    
    <!-- Search -->
    <div style="margin-top: 30px;">
        <input type="search" id="search" placeholder="Search...">
        <button id="search-btn">Search</button>
    </div>
</body>
</html>
"""


# ============================================================================
# FIXTURE LOADER
# ============================================================================

FIXTURES = {
    "simple_login": SIMPLE_LOGIN_FORM,
    "complex_form": COMPLEX_FORM,
    "hidden_elements": HIDDEN_ELEMENTS_PAGE,
    "navigation": NAVIGATION_PAGE,
    "complex_interactive": COMPLEX_INTERACTIVE_PAGE,
}


def get_fixture(name: str) -> str:
    """
    Get HTML fixture by name.
    
    Args:
        name: Fixture name (simple_login, complex_form, etc.)
    
    Returns:
        str: HTML content
    
    Raises:
        KeyError: If fixture not found
    """
    if name not in FIXTURES:
        raise KeyError(f"Fixture '{name}' not found. Available: {list(FIXTURES.keys())}")
    return FIXTURES[name]


def list_fixtures() -> list:
    """Get list of available fixtures."""
    return list(FIXTURES.keys())
