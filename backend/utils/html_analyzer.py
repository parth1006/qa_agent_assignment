"""
HTML Analyzer Module - Extract Structure and Selectors

This module analyzes HTML files to extract structural information
and element selectors for Selenium script generation.

"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from loguru import logger


class HTMLAnalyzer:
    """
    Analyzer for HTML structure and element extraction.
    
    This class provides utilities to:
    - Extract form elements and their attributes
    - Generate CSS selectors and XPath expressions
    - Identify interactive elements (buttons, inputs, links)
    - Extract page structure information
    
    Attributes:
        soup: BeautifulSoup object of parsed HTML
        file_path: Path to HTML file (if loaded from file)
    """
    
    def __init__(self, html_content: Optional[str] = None, file_path: Optional[Path] = None):
        """
        Initialize HTML analyzer.
        
        Args:
            html_content: HTML content as string
            file_path: Path to HTML file (alternative to html_content)
        """
        self.file_path = file_path
        self.soup: Optional[BeautifulSoup] = None
        
        if html_content:
            self.parse_html(html_content)
        elif file_path and file_path.exists():
            self.load_from_file(file_path)
        else:
            logger.warning("No HTML content or file provided")
    
    def load_from_file(self, file_path: Path) -> None:
        """
        Load and parse HTML from file.
        
        Args:
            file_path: Path to HTML file
        """
        logger.info(f"Loading HTML from {file_path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        self.file_path = file_path
        self.parse_html(html_content)
    
    def parse_html(self, html_content: str) -> None:
        """
        Parse HTML content.
        
        Args:
            html_content: HTML content as string
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')
        logger.info(f"✅ HTML parsed successfully")
    
    def get_all_inputs(self) -> List[Dict[str, Any]]:
        """
        Extract all input elements with their attributes.
        
        Returns:
            List of dictionaries containing input element information
        """
        if not self.soup:
            return []
        
        inputs = []
        
        for input_elem in self.soup.find_all('input'):
            input_info = {
                "tag": "input",
                "type": input_elem.get('type', 'text'),
                "id": input_elem.get('id'),
                "name": input_elem.get('name'),
                "class": input_elem.get('class'),
                "placeholder": input_elem.get('placeholder'),
                "value": input_elem.get('value'),
                "required": input_elem.has_attr('required'),
                "selector": self._generate_selector(input_elem)
            }
            inputs.append(input_info)
        
        logger.debug(f"Found {len(inputs)} input elements")
        return inputs
    
    def get_all_buttons(self) -> List[Dict[str, Any]]:
        """
        Extract all button elements.
        
        Returns:
            List of button information dictionaries
        """
        if not self.soup:
            return []
        
        buttons = []
        
        for button in self.soup.find_all(['button', 'input']):
            if button.name == 'input' and button.get('type') not in ['button', 'submit']:
                continue
            
            button_info = {
                "tag": button.name,
                "type": button.get('type', 'button'),
                "id": button.get('id'),
                "class": button.get('class'),
                "text": button.get_text(strip=True) if button.name == 'button' else button.get('value'),
                "onclick": button.get('onclick'),
                "selector": self._generate_selector(button)
            }
            buttons.append(button_info)
        
        logger.debug(f"Found {len(buttons)} button elements")
        return buttons
    
    def get_all_forms(self) -> List[Dict[str, Any]]:
        """
        Extract all form elements and their fields.
        
        Returns:
            List of form information dictionaries
        """
        if not self.soup:
            return []
        
        forms = []
        
        for form in self.soup.find_all('form'):
            form_info = {
                "id": form.get('id'),
                "class": form.get('class'),
                "action": form.get('action'),
                "method": form.get('method', 'get'),
                "selector": self._generate_selector(form),
                "inputs": [],
                "buttons": []
            }
            
            # Find inputs within form
            for input_elem in form.find_all('input'):
                form_info["inputs"].append({
                    "type": input_elem.get('type', 'text'),
                    "id": input_elem.get('id'),
                    "name": input_elem.get('name'),
                    "selector": self._generate_selector(input_elem)
                })
            
            # Find buttons within form
            for button in form.find_all(['button', 'input']):
                if button.name == 'input' and button.get('type') not in ['button', 'submit']:
                    continue
                form_info["buttons"].append({
                    "type": button.get('type', 'button'),
                    "id": button.get('id'),
                    "text": button.get_text(strip=True) if button.name == 'button' else button.get('value'),
                    "selector": self._generate_selector(button)
                })
            
            forms.append(form_info)
        
        logger.debug(f"Found {len(forms)} form elements")
        return forms
    
    def get_all_links(self) -> List[Dict[str, Any]]:
        """
        Extract all link elements.
        
        Returns:
            List of link information dictionaries
        """
        if not self.soup:
            return []
        
        links = []
        
        for link in self.soup.find_all('a'):
            link_info = {
                "tag": "a",
                "id": link.get('id'),
                "class": link.get('class'),
                "href": link.get('href'),
                "text": link.get_text(strip=True),
                "selector": self._generate_selector(link)
            }
            links.append(link_info)
        
        logger.debug(f"Found {len(links)} link elements")
        return links
    
    def find_element_by_text(self, text: str, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find elements containing specific text.
        
        Args:
            text: Text to search for
            tag: Optional tag name to filter by
            
        Returns:
            List of matching elements
        """
        if not self.soup:
            return []
        
        elements = []
        search_tags = [tag] if tag else ['button', 'a', 'span', 'div', 'p', 'h1', 'h2', 'h3', 'label']
        
        for tag_name in search_tags:
            for elem in self.soup.find_all(tag_name):
                if text.lower() in elem.get_text().lower():
                    elements.append({
                        "tag": elem.name,
                        "text": elem.get_text(strip=True),
                        "id": elem.get('id'),
                        "class": elem.get('class'),
                        "selector": self._generate_selector(elem)
                    })
        
        return elements
    
    def _generate_selector(self, element: Tag) -> Dict[str, str]:
        """
        Generate multiple selector types for an element.
        
        Args:
            element: BeautifulSoup Tag element
            
        Returns:
            Dictionary with different selector types
        """
        selectors = {}
        
        # ID selector (highest priority)
        if element.get('id'):
            selectors['id'] = element.get('id')
            selectors['css_id'] = f"#{element.get('id')}"
        
        # Name selector
        if element.get('name'):
            selectors['name'] = element.get('name')
            selectors['css_name'] = f"[name='{element.get('name')}']"
        
        # Class selector
        if element.get('class'):
            classes = element.get('class')
            if isinstance(classes, list):
                classes = ' '.join(classes)
            selectors['class'] = classes
            selectors['css_class'] = f".{'.'.join(element.get('class'))}"
        
        # Generate CSS selector path
        selectors['css'] = self._generate_css_path(element)
        
        # Generate XPath
        selectors['xpath'] = self._generate_xpath(element)
        
        return selectors
    
    def _generate_css_path(self, element: Tag) -> str:
        """
        Generate CSS selector path for element.
        
        Args:
            element: BeautifulSoup Tag element
            
        Returns:
            CSS selector string
        """
        # Prefer ID if available
        if element.get('id'):
            return f"#{element.get('id')}"
        
        # Build path from tag and attributes
        parts = [element.name]
        
        if element.get('class'):
            classes = '.'.join(element.get('class'))
            parts.append(f".{classes}")
        
        return ''.join(parts)
    
    def _generate_xpath(self, element: Tag) -> str:
        """
        Generate XPath for element.
        
        Args:
            element: BeautifulSoup Tag element
            
        Returns:
            XPath string
        """
        # Prefer ID if available
        if element.get('id'):
            return f"//*[@id='{element.get('id')}']"
        
        # Use name if available
        if element.get('name'):
            return f"//{element.name}[@name='{element.get('name')}']"
        
        # Fallback to tag name
        return f"//{element.name}"
    
    def get_page_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the page structure.
        
        Returns:
            Dictionary with page statistics
        """
        if not self.soup:
            return {}
        
        return {
            "title": self.soup.title.string if self.soup.title else None,
            "total_inputs": len(self.soup.find_all('input')),
            "total_buttons": len(self.soup.find_all(['button'])) + 
                           len(self.soup.find_all('input', type=['button', 'submit'])),
            "total_forms": len(self.soup.find_all('form')),
            "total_links": len(self.soup.find_all('a')),
            "total_images": len(self.soup.find_all('img')),
            "has_javascript": bool(self.soup.find_all('script'))
        }
    
    def get_selenium_script_context(self) -> str:
        """
        Generate context string for Selenium script generation.
        
        Returns:
            Formatted string with HTML structure information
        """
        if not self.soup:
            return "No HTML loaded"
        
        context_parts = []
        
        # Page summary
        summary = self.get_page_summary()
        context_parts.append("=== PAGE SUMMARY ===")
        for key, value in summary.items():
            context_parts.append(f"{key}: {value}")
        context_parts.append("")
        
        # Input fields
        inputs = self.get_all_inputs()
        if inputs:
            context_parts.append("=== INPUT FIELDS ===")
            for inp in inputs:
                selector = inp['selector'].get('id') or inp['selector'].get('name') or inp['selector']['css']
                context_parts.append(
                    f"- {inp['type']} input: id='{inp['id']}', "
                    f"name='{inp['name']}', selector='{selector}'"
                )
            context_parts.append("")
        
        # Buttons
        buttons = self.get_all_buttons()
        if buttons:
            context_parts.append("=== BUTTONS ===")
            for btn in buttons:
                selector = btn['selector'].get('id') or btn['selector']['css']
                context_parts.append(
                    f"- Button '{btn['text']}': id='{btn['id']}', selector='{selector}'"
                )
            context_parts.append("")
        
        return "\n".join(context_parts)


# ===== HELPER FUNCTIONS =====
def analyze_html_file(file_path: Path) -> HTMLAnalyzer:
    """
    Quick helper to analyze an HTML file.
    
    Args:
        file_path: Path to HTML file
        
    Returns:
        HTMLAnalyzer instance
    """
    return HTMLAnalyzer(file_path=file_path)


if __name__ == "__main__":
    """Test the HTML Analyzer module."""
    
    # Configure logger
    from pathlib import Path
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/html_analyzer_test.log", rotation="1 MB")
    
    print("\n" + "="*60)
    print("TESTING HTML ANALYZER MODULE")
    print("="*60 + "\n")
    
    # Create test HTML
    test_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <form id="test-form">
            <input type="text" id="username" name="username" placeholder="Username" required>
            <input type="password" id="password" name="password" placeholder="Password">
            <input type="email" id="email" name="email" placeholder="Email">
            <button type="submit" id="submit-btn">Submit</button>
        </form>
        <a href="#" id="link1">Test Link</a>
        <button class="action-btn" onclick="doSomething()">Action</button>
    </body>
    </html>
    """
    
    # Test 1: Parse HTML
    print("Test 1: Parsing HTML...")
    analyzer = HTMLAnalyzer(html_content=test_html)
    print("✅ HTML parsed\n")
    
    # Test 2: Get page summary
    print("Test 2: Getting page summary...")
    summary = analyzer.get_page_summary()
    print("✅ Page summary:")
    for key, value in summary.items():
        print(f"   {key}: {value}")
    print()
    
    # Test 3: Extract inputs
    print("Test 3: Extracting input fields...")
    inputs = analyzer.get_all_inputs()
    print(f"✅ Found {len(inputs)} inputs:")
    for inp in inputs:
        print(f"   - {inp['type']}: id={inp['id']}, name={inp['name']}")
    print()
    
    # Test 4: Extract buttons
    print("Test 4: Extracting buttons...")
    buttons = analyzer.get_all_buttons()
    print(f"✅ Found {len(buttons)} buttons:")
    for btn in buttons:
        print(f"   - {btn['text']}: id={btn['id']}")
    print()
    
    # Test 5: Get Selenium context
    print("Test 5: Generating Selenium context...")
    context = analyzer.get_selenium_script_context()
    print("✅ Context generated:")
    print(context)
    print()
    
    print("="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")