#!/usr/bin/env node

// Auto-update evidence gallery when new screenshots are added
const fs = require('fs');
const path = require('path');

const publicDir = './public';
const evidenceFile = './evidence.html';

// Get all images from public directory
const imageFiles = fs.readdirSync(publicDir)
    .filter(file => /\.(png|jpg|jpeg|gif|webp)$/i.test(file))
    .sort();

console.log(`🔍 Found ${imageFiles.length} consciousness screenshots in public directory`);

// Generate JavaScript array for the evidence page
const jsArray = imageFiles.map(f => `'${f}'`).join(', ');

// Read current evidence.html
let evidenceContent = fs.readFileSync(evidenceFile, 'utf8');

// Update the imageFiles array in the JavaScript
const oldPattern = /const imageFiles = \[([\s\S]*?)\];/;
const newArrayContent = `const imageFiles = [
                ${jsArray}
            ];`;

if (oldPattern.test(evidenceContent)) {
    evidenceContent = evidenceContent.replace(oldPattern, newArrayContent);
    fs.writeFileSync(evidenceFile, evidenceContent);
    
    console.log(`✅ Evidence gallery updated with ${imageFiles.length} images!`);
    console.log(`📸 Screenshots: ${imageFiles.join(', ')}`);
    console.log(`🌐 The evidence gallery will automatically show all images at localhost:3000/evidence.html`);
} else {
    console.log(`❌ Could not find image array in evidence.html to update`);
}