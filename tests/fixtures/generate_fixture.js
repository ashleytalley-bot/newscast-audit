import XLSX from 'xlsx';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const fixturePath = path.join(__dirname, 'test_upload.xlsx');

const data = [
    {
        "Id": 1,
        "Start time": "2023-10-27 10:00:00",
        "Completion time": "2023-10-27 10:05:00",
        "Email": "test@example.com",
        "Name": "Test User",
        "Date of newscast:": "2023-10-27",
        "Which newscast are you auditing?": "Morning",
        "Does the story address the audience as \"you,\" end with \"Here's what you can do today\"?": "Yes"
    },
    {
        "Id": 2,
        "Start time": "2023-10-28 11:00:00",
        "Completion time": "2023-10-28 11:05:00",
        "Email": "test2@example.com",
        "Name": "Test User 2",
        "Date of newscast:": "2023-10-28",
        "Which newscast are you auditing?": "Evening",
        "Does the story address the audience as \"you,\" end with \"Here's what you can do today\"?": "No"
    }
];

const ws = XLSX.utils.json_to_sheet(data);
const wb = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb, ws, "Sheet1");

XLSX.writeFile(wb, fixturePath);
console.log(`✓ Generated fixture at ${fixturePath}`);
