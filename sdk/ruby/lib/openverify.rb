require 'json'
require 'json_schemer'
require 'bigdecimal'

# Offline wire SDK. See README for the explicitly supported semantic subset.
module OpenVerify
  SDK_VERSION = '0.1.0'
  VCP_VERSION = 'draft'
  PROVIDER_CONTRACT_VERSION = '0.1'
  SPEC_REVISION = '5f17f402a270882f244a54dde25eda92a085eb39'
  BUNDLE = JSON.parse(File.read(File.join(__dir__, 'openverify/bundle.json'))).freeze
  class ProtocolError < StandardError
    attr_reader :code, :path
    def initialize(code, message = code, path = '')
      @code, @path = code, path
      super(message)
    end
  end
  # Public JSON object model; absent keys and explicit null remain distinct.
  class WireObject < Hash
    def to_json(*args) = super(*args)
  end
  class StrictHash < Hash
    def []=(key, value)
      raise JSON::ParserError, 'duplicate JSON key' if key?(key)
      super
    end
  end
  def self.check(schema, value, code)
    resolver = ->(uri) { BUNDLE['schemas'].fetch(uri.to_s) { raise ProtocolError.new('INVALID_PROVIDER_OUTPUT', 'Offline unknown reference') } }
    validator = JSONSchemer.schema(numbers(schema), meta_schema: JSONSchemer.draft202012, format: false, ref_resolver: resolver)
    raise ProtocolError.new(code) unless validator.valid?(numbers(value))
  rescue JSONSchemer::InvalidRefResolution, JSONSchemer::UnknownRef => e
    raise ProtocolError.new('INVALID_PROVIDER_OUTPUT', e.message)
  end
  # JSON number equality must not inherit Ruby's Integer/Float hash distinction.
  def self.numbers(value)
    case value
    when Numeric then BigDecimal(value.to_s)
    when Hash then value.transform_values { |v| numbers(v) }
    when Array then value.map { |v| numbers(v) }
    else value
    end
  end
  def self.validate_structure(contract, kind, value)
    prefix = {'vcp'=>'urn:verification:draft:', 'provider'=>'urn:openverify:provider:0.1:'}[contract]
    raise ProtocolError.new('SDK_UNSUPPORTED') unless prefix && (schema = BUNDLE['schemas'][prefix + kind])
    if contract == 'vcp' && value.is_a?(Hash) && value.key?('protocol') && value['protocol'] != 'draft'
      raise ProtocolError.new('PROTOCOL_VERSION')
    end
    if contract == 'provider' && kind == 'invocation' && value.is_a?(Hash) && value.key?('contract_version') && value['contract_version'] != '0.1'
      raise ProtocolError.new('CONTRACT_VERSION_UNSUPPORTED')
    end
    check(schema, value, contract == 'vcp' ? 'PROTOCOL_STRUCTURE' : kind == 'invocation' ? 'INVALID_INVOCATION' : 'INVALID_PROVIDER_OUTPUT')
  end
  def self.validate_data(schema, value, code = 'INVALID_INPUT')
    positions, refs = {}, []
    visit = nil
    visit = lambda do |s, path, top|
      positions[path] = true
      next if s == true || s == false
      raise ProtocolError.new('INVALID_PROVIDER_OUTPUT') unless s.is_a?(Hash)
      if (!top && s.key?('$id')) || %w[$anchor $dynamicAnchor $dynamicRef].any? { |k| s.key?(k) }
        raise ProtocolError.new('INVALID_PROVIDER_OUTPUT')
      end
      raise ProtocolError.new('INVALID_PROVIDER_OUTPUT') if s.key?('$schema') && s['$schema'] != 'https://json-schema.org/draft/2020-12/schema'
      if s.key?('$ref')
        ref = s['$ref']
        raise ProtocolError.new('INVALID_PROVIDER_OUTPUT') unless ref.is_a?(String) && (ref == '#' || ref.start_with?('#/'))
        refs << ref[1..]
      end
      %w[properties patternProperties $defs dependentSchemas].each do |k|
        s.fetch(k, {}).each { |name, v| visit.call(v, "#{path}/#{k}/#{name.gsub('~','~0').gsub('/','~1')}", false) } if s.fetch(k, {}).is_a?(Hash)
      end
      %w[additionalProperties unevaluatedProperties propertyNames contains items unevaluatedItems not if then else contentSchema].each { |k| visit.call(s[k], "#{path}/#{k}", false) if s.key?(k) }
      %w[allOf anyOf oneOf prefixItems].each { |k| s.fetch(k, []).each_with_index { |v, n| visit.call(v, "#{path}/#{k}/#{n}", false) } if s.fetch(k, []).is_a?(Array) }
    end
    visit.call(schema, '', true)
    raise ProtocolError.new('INVALID_PROVIDER_OUTPUT') unless refs.all? { |r| positions[r] }
    validator = JSONSchemer.schema(numbers(schema), meta_schema: JSONSchemer.draft202012, format: false, ref_resolver: ->(_) { raise ProtocolError.new('INVALID_PROVIDER_OUTPUT') })
    raise ProtocolError.new('INVALID_PROVIDER_OUTPUT') unless validator.valid_schema?
    raise ProtocolError.new(code) unless validator.valid?(numbers(value))
  end
  def self.validate(contract, kind, value)
    validate_structure(contract, kind, value)
    raise ProtocolError.new('SDK_UNSUPPORTED') if contract == 'vcp' && !BUNDLE['semantic_vcp_types'].include?(kind)
    BUNDLE['rules'].fetch(kind, []).each { |r| check(r['schema'], value, contract == 'provider' ? 'INVALID_PROVIDER_OUTPUT' : r['code']) }
    if kind == 'resource' && value['kind'] == 'RANGE' && value['minimum'] > value['maximum']
      raise ProtocolError.new('RESOURCE_MEASUREMENT')
    end
    if contract == 'vcp'
      {'extensions'=>'extension', 'evidence'=>'evidence'}.each { |k, target| value.fetch(k, []).each { |v| validate('vcp', target, v) } }
      validate('vcp', 'artifact-ref', value['artifact_ref']) if value['artifact_ref']
      value.fetch('usage', {}).each_value { |v| validate('vcp', 'resource', v) }
    else
      raise ProtocolError.new('SDK_UNSUPPORTED') if value.key?('deadline') || value.key?('timestamp')
      if kind == 'provider-event'
        begin
          target = {'evidence'=>'evidence','artifact'=>'artifact-ref'}[value['kind']]
          validate('vcp',target,value['payload']) if target
          value['payload'].each_value { |r| validate('vcp','resource',r) } if value['kind'] == 'resource_usage'
        rescue ProtocolError
          raise ProtocolError.new('INVALID_PROVIDER_OUTPUT')
        end
      end
      if kind == 'provider-manifest'
        seen = {}
        value['capabilities'].each do |c|
          key = [c['capability_id'], c['capability_version']]
          raise ProtocolError.new('INVALID_PROVIDER_OUTPUT') if seen[key]
          seen[key] = true
          raise ProtocolError.new('INVALID_PROVIDER_OUTPUT') if c.key?('vcp_version') && !value['supported_vcp_versions'].include?(c['vcp_version'])
          validate('provider', 'capability', c)
        end
      end
      if kind == 'capability'
        %w[input_schema config_schema output_schema].each do |k|
          begin
            validate_data(value[k], nil)
          rescue ProtocolError => e
            raise unless e.code == 'INVALID_INPUT'
          end
        end
      end
      validate('provider', 'provider-manifest', value['manifest']) if kind == 'initialize-result'
      raise ProtocolError.new(kind == 'invocation' ? 'INVALID_INVOCATION' : 'INVALID_PROVIDER_OUTPUT') if value.key?('vcp_version') && value['vcp_version'] != 'draft'
      %w[resource_budget resource_usage].each do |k|
        value.fetch(k, {}).each_value do |r|
          begin
            validate('vcp', 'resource', r)
          rescue ProtocolError
            raise ProtocolError.new(kind == 'invocation' ? 'INVALID_INVOCATION' : 'INVALID_PROVIDER_OUTPUT')
          end
          raise ProtocolError.new('INVALID_INVOCATION') if k == 'resource_budget' && (r['kind'] != 'EXACT' || value['vcp_version'] != 'draft')
        end
      end
    end
    WireObject[value]
  end
  def self.parse(contract, kind, text)
    begin
      value = JSON.parse(text, object_class: StrictHash, allow_nan: false, allow_duplicate_key: false)
      precise = JSON.parse(text, decimal_class: BigDecimal, allow_nan: false, allow_duplicate_key: false)
      faithful = lambda do |native, exact|
        if native.is_a?(Float)
          raise JSON::ParserError, 'JSON number cannot be represented faithfully' unless native.finite? && BigDecimal(native.to_s) == exact
        elsif native.is_a?(Hash)
          native.each { |k, v| faithful.call(v, exact[k]) }
        elsif native.is_a?(Array)
          native.each_with_index { |v, n| faithful.call(v, exact[n]) }
        end
      end
      faithful.call(value, precise)
    rescue JSON::ParserError, EncodingError => e
      raise ProtocolError.new(contract == 'vcp' ? 'PROTOCOL_JSON' : kind == 'invocation' ? 'INVALID_INVOCATION' : 'INVALID_PROVIDER_OUTPUT', e.message)
    end
    validate(contract, kind, value)
  end
  def self.serialize(value) = JSON.generate(value, allow_nan: false)
end
