require 'minitest/autorun'
require_relative '../lib/verifyanything'
class SharedTest < Minitest::Test
  ROOT = File.expand_path('../../../conformance/sdk', __dir__)
  JSON.parse(File.read(File.join(ROOT, 'manifest.json')))['cases'].each do |path|
    c = JSON.parse(File.read(File.join(ROOT, path)))
    define_method("test_#{c['id']}") do
      action = lambda { c['operation'] == 'data' ? (VerifyAnything.validate_data(c['schema'], c['input']); c['input']) : VerifyAnything.parse(c['contract'], c['type'], JSON.generate(c['input'])) }
      if c['expected']['accepted']
        value = action.call
        assert_equal c['expected']['normalized'], JSON.parse(VerifyAnything.serialize(value))
      else
        e = assert_raises(VerifyAnything::ProtocolError, &action)
        assert_equal c['expected']['error'], e.code unless c['expected']['error'] == '*'
      end
    end
  end
  def test_duplicate
    assert_equal 'PROTOCOL_JSON', assert_raises(VerifyAnything::ProtocolError) { VerifyAnything.parse('vcp','result','{"protocol":"draft","protocol":"draft"}') }.code
  end
  def test_numeric_overflow
    assert_raises(VerifyAnything::ProtocolError) { VerifyAnything.parse('provider','outcome','{"invocation_id":"i","state":"COMPLETED","output":1e400}') }
  end
end
