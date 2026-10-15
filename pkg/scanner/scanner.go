package scanner

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

type FileStats struct {
	Path        string   `json:"path"`
	Language    string   `json:"language"`
	LinesCount  int      `json:"lines_count"`
	SizeBytes   int64    `json:"size_bytes"`
	SecretHits  []string `json:"secret_hits,omitempty"`
}

var (
	awsKeyRegex    = regexp.MustCompile(`\b(AKIA[0-9A-Z]{16})\b`)
	privKeyRegex   = regexp.MustCompile(`-----BEGIN (?:RSA |EC )?PRIVATE KEY-----`)
	jwtRegex       = regexp.MustCompile(`\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+\b`)
)

func ScanFile(root, path string) (*FileStats, error) {
	info, err := os.Stat(path)
	if err != nil {
		return nil, err
	}

	content, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	lines := 0
	for _, b := range content {
		if b == '\n' {
			lines++
		}
	}

	rel, _ := filepath.Rel(root, path)
	ext := strings.ToLower(filepath.Ext(path))

	stats := &FileStats{
		Path:       rel,
		Language:   ext,
		LinesCount: lines,
		SizeBytes:  info.Size(),
	}

	// High speed Go secret check
	if awsKeyRegex.Match(content) {
		stats.SecretHits = append(stats.SecretHits, "AWS_ACCESS_KEY")
	}
	if privKeyRegex.Match(content) {
		stats.SecretHits = append(stats.SecretHits, "PRIVATE_KEY")
	}

	return stats, nil
}
