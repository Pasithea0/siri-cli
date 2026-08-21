# Homebrew formula for siribridge.
#
# Install (once a release tag + tarball exist on GitHub):
#   brew tap <your-org>/homebrew-siribridge
#   brew install <your-org>/siribridge/siribridge
#
# Or build from source with a local checkout:
#   brew install --build-from-source --formula Formula/siribridge.rb
#
# This exposes the `siri` command on your PATH.

class Siribridge < Formula
  include Language::Python::Virtualenv

  desc "Ask the real macOS Siri from the terminal and read back its response"
  homepage "https://github.com/your-org/siribridge" # TODO: set real repo URL before publishing
  # TODO: after creating a v0.1.0 GitHub release, set the real tarball URL
  # and run `brew formula` / `brew audit` to fill the real sha256.
  url "https://github.com/your-org/siribridge/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
  license "MIT"

  # Requires macOS 27 (Tahoe) for the new "Siri AI" app; the macOS 26 overlay
  # has an empty Accessibility tree and cannot return responses.
  depends_on :macos
  depends_on "python@3.12"

  def install
    # Create an isolated venv and pip-install the package + deps (pyobjc,
    # click, mcp) from PyPI. The `siri` console script lands in libexec/bin.
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install buildpath
    bin.install_symlink libexec/"bin/siri"
  end

  def caveats
    <<~EOS
      siribridge reads the macOS Siri AI app via the Accessibility API.

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
