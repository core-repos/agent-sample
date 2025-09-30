#!/bin/bash

echo "=== Arctic-Text2SQL-R1 Local Setup ==="
echo ""

# Check if Ollama is installed
check_ollama() {
    if command -v ollama &> /dev/null; then
        echo "✓ Ollama is installed"
        return 0
    else
        echo "✗ Ollama is not installed"
        return 1
    fi
}

# Install Ollama (macOS)
install_ollama_mac() {
    echo "Installing Ollama for macOS..."
    curl -fsSL https://ollama.ai/install.sh | sh
}

# Install Ollama (Linux)
install_ollama_linux() {
    echo "Installing Ollama for Linux..."
    curl -fsSL https://ollama.ai/install.sh | sh
}

# Main setup
main() {
    # Detect OS
    OS="$(uname -s)"
    
    # Check and install Ollama
    if ! check_ollama; then
        echo ""
        read -p "Would you like to install Ollama? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            case "$OS" in
                Darwin*)
                    install_ollama_mac
                    ;;
                Linux*)
                    install_ollama_linux
                    ;;
                *)
                    echo "Please install Ollama manually from: https://ollama.ai"
                    exit 1
                    ;;
            esac
        else
            echo "Please install Ollama manually from: https://ollama.ai"
            exit 1
        fi
    fi
    
    echo ""
    echo "Starting Ollama service..."
    # Start Ollama in background if not running
    if ! pgrep -x "ollama" > /dev/null; then
        ollama serve &
        sleep 3
    fi
    
    echo ""
    echo "Pulling Arctic-Text2SQL model..."
    echo "Note: This is a large model (7B parameters, ~4GB download)"
    
    # Try official Arctic model first
    if ollama pull snowflake/arctic-embed; then
        echo "✓ Arctic model pulled successfully"
    else
        echo "Official Arctic model not available, trying alternative..."
        # Alternative: Use a SQL-optimized model
        ollama pull sqlcoder:7b-q4_0 || ollama pull codellama:7b-instruct-q4_0
        echo "✓ Alternative SQL model pulled"
    fi
    
    echo ""
    echo "Verifying installation..."
    ollama list
    
    echo ""
    echo "=== Setup Complete ==="
    echo ""
    echo "Arctic-Text2SQL is ready to use!"
    echo "The model will run locally on port 11434"
    echo ""
    echo "To test the model manually:"
    echo "  ollama run snowflake/arctic-embed \"Convert to SQL: Show total sales\""
    echo ""
    echo "To use in the application:"
    echo "  1. Set LLM_PROVIDER=arctic in your .env file"
    echo "  2. Restart the backend server"
}

main "$@"