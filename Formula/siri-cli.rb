# Homebrew formula for siri-cli.
#
# Install:
#   brew tap Pasithea0/homebrew-siri-cli
#   brew install siri-cli
#
# This exposes the `siri` command on your PATH.

class SiriCli < Formula
  include Language::Python::Virtualenv

  desc "Ask the real macOS Siri from the terminal and read back its response"
  homepage "https://github.com/Pasithea0/siri-cli"
  url "https://github.com/Pasithea0/siri-cli/archive/refs/tags/v1.1.0.tar.gz"
  sha256 "87f3606179e078259d29ada572aecba58294a4f1ee8bbf329dfa359d8d27ddde"
  license "MIT"

  # Requires macOS 27 (Tahoe) for the new "Siri AI" app; the macOS 26 overlay
  # has an empty Accessibility tree and cannot return responses.
  depends_on :macos
  depends_on "python@3.12"

  resource "click" do
    url "https://files.pythonhosted.org/packages/76/d4/81420972a676e8ffea40450d8c8c92943e7218a78fe9b64359836cc9876b/click-8.4.2.tar.gz"
    sha256 "9a6cea6e60b17ebe0a44c5cc636d94f09bd66142c1cd7d8b4cd731c4917a15f6"
  end

  resource "pyobjc-core" do
    url "https://files.pythonhosted.org/packages/a5/78/abc4ce5920305780aeb36b4067a86253378b36e29ba96673a3deb02eb03a/pyobjc_core-12.2.2.tar.gz"
    sha256 "3906452339cd06a3bb07df103c2511d4cb0f7a22d8771c0b802eba15d9a642b6"
  end

  resource "pyobjc-framework-Cocoa" do
    url "https://files.pythonhosted.org/packages/75/76/49c6da2c6a831020b4854ba20079d5a1030474bffc776b7b73c2eeff8c15/pyobjc_framework_cocoa-12.2.2.tar.gz"
    sha256 "c96c0ef69a71afbbb0e6a7d594b455c5fe47d62e0db376ee7a2b4b828c16ace9"
  end

  resource "pyobjc-framework-Quartz" do
    url "https://files.pythonhosted.org/packages/35/b1/426a37c7ae37280b3ffca2571fb48f211946aee2f4ca31a603ed1943c4a7/pyobjc_framework_quartz-12.2.2.tar.gz"
    sha256 "810f97b210cfd93704d240860286dfd6df09f9f1c52525fc5c2166723aea3f9e"
  end

  resource "pyobjc-framework-CoreText" do
    url "https://files.pythonhosted.org/packages/6d/66/405006d3502ffcd3bc69e0b7249ab7c05a5b43a07fa3959ce6b2a84f3278/pyobjc_framework_coretext-12.2.2.tar.gz"
    sha256 "64ddc02303217028e32e22c7cc00b5112d84e9d9a67c37d00c2e54f9172284ab"
  end

  resource "pyobjc-framework-CoreML" do
    url "https://files.pythonhosted.org/packages/b7/3b/c835535e7aef41afc953e5597ea41e693b7bae80d753ab74b9721e07cba5/pyobjc_framework_coreml-12.2.2.tar.gz"
    sha256 "3e6abe134634adbcc0c1e843826e42df86e63beb3bc7e8e4a914e93179ae1e75"
  end

  resource "pyobjc-framework-ApplicationServices" do
    url "https://files.pythonhosted.org/packages/29/40/b792ecc88a9fa639318509c127f0b153cd334bd27b47df373f4b7362a36d/pyobjc_framework_applicationservices-12.2.2.tar.gz"
    sha256 "0bcc09531d5854598fd74706d999e4ae3b7c503204d318910d02eba30e8eecef"
  end

  resource "pyobjc-framework-Vision" do
    url "https://files.pythonhosted.org/packages/ea/bf/31e8bcae94047b365592ab7533096a4025c0306a8a312b65bcbf57e073ec/pyobjc_framework_vision-12.2.2.tar.gz"
    sha256 "a6bf78e8dca145c6a78fd8d5f925b6da54649a60a1464b81ff405bca4a08406b"
  end

  def install
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install resources
    venv.pip_install_and_link buildpath
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
