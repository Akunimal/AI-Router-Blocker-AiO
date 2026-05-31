class AiDevsecGateway < Formula
  desc "Take back control. Intercept, audit, and route your AI traffic"
  homepage "https://github.com/Akunimal/AI-Router-Blocker-AiO"
  url "https://github.com/Akunimal/AI-Router-Blocker-AiO/archive/refs/heads/main.tar.gz"
  version "1.3.2"
  license "MIT"

  depends_on "python@3.12"

  def install
    # Install files into celler directory
    libexec.install Dir["ai_blocker"]
    libexec.install "ai_blocker.py"
    libexec.install "translations.json"
    
    # Create the launcher script
    (bin/"ai-devsec-gateway").write <<~EOS
      #!/bin/bash
      exec "#{Formula["python@3.12"].opt_bin}/python3" "#{libexec}/ai_blocker.py" "$@"
    EOS
  end

  test do
    assert_match "Status:", shell_output("#{bin}/ai-devsec-gateway --status")
  end
end
