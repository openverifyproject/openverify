Gem::Specification.new do |s|
  s.name = 'openverify-sdk'
  s.version = '0.1.0'
  s.summary = 'OpenVerify DRAFT VCP and Provider Contract wire SDK'
  s.authors = ['OpenVerify contributors']
  s.homepage = 'https://github.com/openverifyproject/openverify'
  s.license = 'MIT'
  s.required_ruby_version = '>= 3.2'
  s.files = Dir['lib/**/*', 'LICENSE', 'README.md']
  s.require_paths = ['lib']
  s.metadata = {'source_code_uri' => s.homepage, 'rubygems_mfa_required' => 'true'}
  s.add_dependency 'json_schemer', '~> 2.5'
end
