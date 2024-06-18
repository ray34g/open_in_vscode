# Open in VSCode

## Feature

- Create and update embedded Javascript in the SVG file using Visual Studio Code.

## How it works

This extension creates temporary directory and files so that other program can edit them.

```xml
  <script id="script1" data-editor-tempdir="C:\Users\user\AppData\Local\Temp\inkscape-vscode-n_os9w_l"/>
  <style id="style1" data-editor-tempdir="C:\Users\user\AppData\Local\Temp\inkscape-vscode-n_os9w_l"/>
```



```mermaid
%%{init: {'securityLevel':'antiscript'}}%%
sequenceDiagram
    autonumber

    participant inkscape as Inkscape
    participant os as OS
    participant vscode as Visual Studio Code

    inkscape->>os: Create temporary directory for the editor
    inkscape->>inkscape: Mark script node as editting using data attribute
    inkscape->>os: Save script node content as "*.js" file
    Note right of inkscape: script1.js, script2.js,,
    inkscape->>vscode: Start VS Code process
    vscode->>os: Update script files in temporary directory
    inkscape->>os: Get Updated script files
    inkscape->>inkscape: Remove data attribute from script node
    inkscape->>inkscape: Save file content as svg node.
    
```

## License

MIT License

