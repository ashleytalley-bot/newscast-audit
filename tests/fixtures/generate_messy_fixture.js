import XLSX from 'xlsx';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const fixturePath = path.join(__dirname, 'messy_upload.xlsx');

const data = [
    {
        "Id": 1,
        "Start time": "2023-11-01 10:00:00",
        "Completion time": "2023-11-01 10:05:00",
        "Email": "messy@example.com",
        "Name": "Messy User",
        "Date of newscast:": "2023-11-01",
        "Which newscast are you auditing?": "Nightly News", // Unrecognized
        "Does the story address the audience as \"you,\" end with \"Here's what you can do today\"?": "Maybe", // Unexpected value
        "Extra Column": "This should be ignored" // Ignored column
    }
];

const ws = XLSX.utils.json_to_sheet(data);
const wb = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb, ws, "Sheet1");

XLSX.writeFile(wb, fixturePath);
console.log(`✓ Generated messy fixture at ${fixturePath}`);
