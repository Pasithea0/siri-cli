# Homebrew formula for siri-cli.
#
# Install:
#   brew tap Pasithea0/homebrew-siri-cli
#   brew install Pasithea0/siri-cli/siri-cli
#
# Or build from source with a local checkout:
#   brew install --build-from-source --formula Formula/siri-cli.rb
#
# This exposes the `siri` command on your PATH.

class SiriCli < Formula
  include Language::Python::Virtualenv

  desc "Ask the real macOS Siri from the terminal and read back its response"
  homepage "https://github.com/Pasithea0/siri-cli"
  # The URL/sha256 are filled by the release workflow (semantic-release)
  # via @semantic-release/exec after tagging. Template below:
  url "https://github.com/Pasithea0/siri-cli/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "9892aa5e679caf326b847e3ba77ac42724e880977f58d9c648c111ff065d5e4b"
  license "MIT"

  # Requires macOS 27 (Tahoe) for the new "Siri AI" app; the macOS 26 overlay
  # has an empty Accessibility tree and cannot return responses.
  depends_on :macos
  depends_on "python@3.12"

  def install
    # Create an isolated venv and pip-install the package + deps (pyobjc,
    # click) from PyPI. The `siri` console script lands in libexec/bin.
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install buildpath
    bin.install_symlink libexec/"bin/siri"
  end

  def caveats
    <<~EOS
      siri-cli reads the macOS Siri AI app via the Accessibility API.

      After installing, grant Accessibility (and optionally Screen Recording)
      to the terminal/app that runs `siri`:
        System Settings → Privacy & Security → Accessibility
      Then fully quit and relaunch that terminal so the grant takes effect.

      Verify with:  siri status
    EOS
  end

  test do
    assert_match "Usage:", shell_output("#{bin}/siri --help")
  end
end
