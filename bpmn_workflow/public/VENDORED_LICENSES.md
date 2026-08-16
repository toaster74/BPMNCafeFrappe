# Vendored assets

This app vendors the following open-source libraries under `public/`:

## bpmn-js
- Version: 18.24.0
- License: MIT
- Homepage: https://bpmn.io/toolkit/bpmn-js/
- Files:
  - `public/js/bpmn-js/bpmn-viewer.production.min.js`
  - `public/css/vendor/bpmn-js.css`
  - `public/css/vendor/diagram-js.css`
  - `public/css/vendor/bpmn-embedded.css`

To update:

```bash
npm install bpmn-js
cp node_modules/bpmn-js/dist/bpmn-viewer.production.min.js bpmn_workflow/public/js/bpmn-js/
cp node_modules/bpmn-js/dist/assets/bpmn-js.css bpmn_workflow/public/css/vendor/
cp node_modules/bpmn-js/dist/assets/diagram-js.css bpmn_workflow/public/css/vendor/
cp node_modules/bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css bpmn_workflow/public/css/vendor/
```

### bpmn-js MIT License

```
The MIT License

Copyright (c) 2014-present camunda services GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

## jsPDF + svg2pdf.js
- jsPDF Version: 3.x
- svg2pdf.js Version: 2.7.0
- License: MIT (both)
- Homepages:
  - https://github.com/parallax/jsPDF
  - https://github.com/yWorks/svg2pdf.js
- Files:
  - `public/js/bpmn-pdf/bpmn-pdf.min.js`

The bundle is created with esbuild (IIFE) and exposes `window.BPMNPDF`
(`{ jsPDF, svg2pdf }`).

To update:

```bash
npm install jspdf svg2pdf.js esbuild
# entry.js:
#   import { jsPDF } from 'jspdf';
#   import * as svg2pdf from 'svg2pdf.js/dist/svg2pdf.es.min.js';
#   const svgToPdf = svg2pdf.default || svg2pdf.svg2pdf || svg2pdf;
#   window.BPMNPDF = { jsPDF, svg2pdf: svgToPdf };
npx esbuild entry.js --bundle --format=iife \
  --outfile=bpmn_workflow/public/js/bpmn-pdf/bpmn-pdf.min.js --minify
```

### jsPDF MIT License

```
Copyright (c) 2010-2023 James Hall and contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

### svg2pdf.js MIT License

```
The MIT License

Copyright (c) 2017-present yWorks GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
## bpmn-auto-layout
- Version: 2.0.0-alpha.2 (bundled with esbuild for the browser)
- License: MIT
- Homepage: https://github.com/bpmn-io/bpmn-auto-layout
- Files:
  - `public/js/bpmn-auto-layout/bpmn-auto-layout.min.js`

To update:

```bash
npm install bpmn-auto-layout@2.0.0-alpha.2
npm install esbuild
npx esbuild node_modules/bpmn-auto-layout/dist/index.js \
  --bundle --format=iife --global-name=BpmnAutoLayout \
  --outfile=bpmn_workflow/public/js/bpmn-auto-layout/bpmn-auto-layout.min.js --minify
```

### bpmn-auto-layout MIT License

```
The MIT License

Copyright (c) 2016-present bpmn.io contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
```