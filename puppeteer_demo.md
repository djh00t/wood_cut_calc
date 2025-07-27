# Puppeteer MCP Server Demo

This document contains example code that demonstrates how to use the Puppeteer MCP server tools.

## Examples

### 1. Navigate to a website
```
<use_mcp_tool>
<server_name>github.com/modelcontextprotocol/servers/tree/main/src/puppeteer</server_name>
<tool_name>puppeteer_navigate</tool_name>
<arguments>
{
  "url": "https://example.com"
}
</arguments>
</use_mcp_tool>
```

### 2. Take a screenshot
```
<use_mcp_tool>
<server_name>github.com/modelcontextprotocol/servers/tree/main/src/puppeteer</server_name>
<tool_name>puppeteer_screenshot</tool_name>
<arguments>
{
  "name": "example_screenshot",
  "width": 1024,
  "height": 768
}
</arguments>
</use_mcp_tool>
```

### 3. Execute JavaScript
```
<use_mcp_tool>
<server_name>github.com/modelcontextprotocol/servers/tree/main/src/puppeteer</server_name>
<tool_name>puppeteer_evaluate</tool_name>
<arguments>
{
  "script": "document.title"
}
</arguments>
</use_mcp_tool>
```

### 4. Click an element
```
<use_mcp_tool>
<server_name>github.com/modelcontextprotocol/servers/tree/main/src/puppeteer</server_name>
<tool_name>puppeteer_click</tool_name>
<arguments>
{
  "selector": "a"
}
</arguments>
</use_mcp_tool>
```

### 5. Fill a form field
```
<use_mcp_tool>
<server_name>github.com/modelcontextprotocol/servers/tree/main/src/puppeteer</server_name>
<tool_name>puppeteer_fill</tool_name>
<arguments>
{
  "selector": "input[type=text]",
  "value": "Hello, Puppeteer!"
}
</arguments>
</use_mcp_tool>
```

## How to use these examples

1. Make sure VSCode has been restarted to apply the MCP settings changes
2. Copy and paste the example code to test the functionality
3. Each example demonstrates a different Puppeteer capability

The Puppeteer MCP server allows you to automate browser interactions, take screenshots, and execute JavaScript in a real browser environment.
