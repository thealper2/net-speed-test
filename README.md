# Net Speed Test

A Python command-line tool for measuring internet connection performance metrics.

## :dart: Features

- **Ping Test**: Measures network latency
- **Jitter Test**: Measures stability of network latency
- **Download Test**: Measures download speed
- **Upload Test**: Measures upload speed
- **Multiple Output Formats**: Results can be displayed as text, JSON, or CSV

## :hammer_and_wrench: Installation

1. Clone this repository:
   ```
   git clone https://github.com/thealper2/net-speed-test.git
   cd net-speed-test
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

## :joystick: Usage

Basic usage:

```
python3 speed_test.py
```

This will run all tests with default settings and display the results as text.

### Command-line Options

```
python3 speed_test.py --help
```

Available options:

- `--url`: URL of the speed test server (default: https://speed.cloudflare.com/__down)
- `--download-size`: Size of download test in MB (default: 10)
- `--upload-size`: Size of upload test in MB (default: 5)
- `--ping-count`: Number of ping measurements for latency test (default: 10)
- `--jitter-samples`: Number of samples for jitter measurement (default: 20)
- `--output`: Output format (text, json, csv) (default: text)
- `--verbose`: Enable verbose output
- `--timeout`: Timeout for network operations in seconds (default: 30)

## :handshake: Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch for your feature (git checkout -b feature/your-feature)
3. Commit your changes (git commit -am 'Add some feature')
4. Push to the branch (git push origin feature/your-feature)
5. Create a new Pull Request

## :scroll: License

This project is licensed under the MIT License - see the LICENSE file for details.
