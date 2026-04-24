@echo off
echo 🚀 Launching Portfolio Compass Presentation...

:: 1. Start Backend in a new window
start "Portfolio Compass Backend" cmd /k "python api.py"

:: 2. Start Frontend in a new window
cd frontend
start "Portfolio Compass UI" cmd /k "npm run dev"

:: 3. Open Explainer in default browser
cd ..
start "" "explainer.html"

echo.
echo ✅ Done! 
echo.
echo 1. The Explainer (Presentation Deck) should be open in your browser.
echo 2. The App will be live at http://localhost:3000 once Vite starts up.
echo.
echo Keep the terminal windows open during your presentation.
pause
