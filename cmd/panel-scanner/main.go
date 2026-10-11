package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type FileMetadata struct {
	Path       string `json:"path"`
	Language   string `json:"language"`
	LinesCount int    `json:"lines_count"`
	SizeBytes  int64  `json:"size_bytes"`
}

type ScanOutput struct {
	Source       string         `json:"source"`
	ScannedAt    string         `json:"scanned_at"`
	TotalFiles   int            `json:"total_files"`
	TotalLines   int            `json:"total_lines"`
	Languages    map[string]int `json:"languages"`
	Files        []FileMetadata `json:"files"`
}

var extMap = map[string]string{
	".py":   "Python",
	".go":   "Go",
	".rs":   "Rust",
	".ts":   "TypeScript",
	".js":   "JavaScript",
	".java": "Java",
	".c":    "C",
	".cpp":  "C++",
	".cs":   "C#",
	".rb":   "Ruby",
	".sh":   "Shell",
	".tf":   "Terraform",
	".yaml": "YAML",
	".yml":  "YAML",
	".json": "JSON",
}

func countLines(content []byte) int {
	lines := 0
	for _, b := range content {
		if b == '\n' {
			lines++
		}
	}
	return lines
}

func main() {
	targetDir := flag.String("path", ".", "Target repository directory to scan")
	maxFiles := flag.Int("max-files", 100, "Maximum files to inspect")
	flag.Parse()

	absPath, err := filepath.Abs(*targetDir)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error resolving path: %v\n", err)
		os.Exit(1)
	}

	output := ScanOutput{
		Source:     absPath,
		ScannedAt:  time.Now().UTC().Format(time.RFC3339),
		Languages:  make(map[string]int),
		Files:      make([]FileMetadata, 0),
	}

	err = filepath.WalkDir(absPath, func(path string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return nil
		}
		if d.IsDir() {
			name := d.Name()
			if strings.HasPrefix(name, ".") || name == "node_modules" || name == "vendor" || name == "__pycache__" {
				return filepath.SkipDir
			}
			return nil
		}
		if len(output.Files) >= *maxFiles {
			return filepath.SkipAll
		}

		ext := strings.ToLower(filepath.Ext(path))
		lang, exists := extMap[ext]
		if !exists {
			if strings.ToLower(d.Name()) == "dockerfile" {
				lang = "Dockerfile"
			} else {
				return nil
			}
		}

		info, err := d.Info()
		if err != nil || info.Size() > 512*1024 {
			return nil
		}

		content, err := os.ReadFile(path)
		if err != nil {
			return nil
		}

		lines := countLines(content)
		relPath, _ := filepath.Rel(absPath, path)

		meta := FileMetadata{
			Path:       relPath,
			Language:   lang,
			LinesCount: lines,
			SizeBytes:  info.Size(),
		}

		output.Files = append(output.Files, meta)
		output.Languages[lang]++
		output.TotalLines += lines
		output.TotalFiles++

		return nil
	})

	if err != nil {
		fmt.Fprintf(os.Stderr, "Walk error: %v\n", err)
	}

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	encoder.Encode(output)
}
