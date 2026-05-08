# Diagrams Folder

This directory contains Mermaid source files (.mmd) and generated images.

## How to Add a New Diagram

1. Add your Mermaid file to diagrams/, for example:
   - diagrams/my_new_diagram.mmd
2. Run the conversion command below to generate a high-resolution PNG.

## Recommended Conversion Command

Use this command from the repository root:

`cmd
set  PUPPETEER_EXECUTABLE_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
npx @mermaid-js/mermaid-cli -i diagrams\my_new_diagram.mmd -o diagrams\my_new_diagram_hires.png -w 2400 -H 1800 -s 2
`

## Batch Convert All .mmd Files

If you want to convert every Mermaid file in diagrams/ to a high-resolution PNG, run:

`cmd
set PUPPETEER_EXECUTABLE_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
for %F in (diagrams\*.mmd) do npx @mermaid-js/mermaid-cli -i %F -o %~dpnF_hires.png -w 2400 -H 1800 -s 2
`

> Note: In PowerShell, use $env:PUPPETEER_EXECUTABLE_PATH='C:\Program Files\Google\Chrome\Application\chrome.exe' instead of set.

## Install Mermaid CLI Once

If you have not installed Mermaid CLI in this repo yet, run:

`cmd
npm install @mermaid-js/mermaid-cli --save-dev
`

## Notes

- -w 2400 -H 1800 sets a larger canvas size.
- -s 2 increases render scaling for sharper output.
- Output files are named with _hires.png to avoid overwriting the low-res originals.
