const express = require('express');
const path = require('path');
const app = express();
const port = process.env.PORT || 8080;

// Force your Node app to serve all your HTML, CSS, and JS game assets
app.use(express.static(path.join(__dirname, 'public'))); 

// Fallback to load your main game landing index page
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(port, () => {
  console.log(`Geology game actively tracking on port ${port}`);
});
