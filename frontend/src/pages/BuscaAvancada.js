import React, { useState, useCallback, useRef } from 'react';
import {
  Card,
  Form,
  Input,
  DatePicker,
  Select,
  Button,
  Row,
  Col,
  Table,
  Space,
  Tag,
  message,
  AutoComplete,
} from 'antd';
import { SearchOutlined, DownloadOutlined, ShopOutlined, ImportOutlined, ExportOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { buscaAPI, empresasAPI } from '../services/api';

// Função debounce simples
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

const { RangePicker } = DatePicker;
const { Option } = Select;

const BuscaAvancada = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 100,
    total: 0,
  });
  const [importadorasOptions, setImportadorasOptions] = useState([]);
  const [exportadorasOptions, setExportadorasOptions] = useState([]);
  const [loadingImportadoras, setLoadingImportadoras] = useState(false);
  const [loadingExportadoras, setLoadingExportadoras] = useState(false);

  const ufs = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
  ];

  const viasTransporte = [
    'MARITIMA',
    'AEREA',
    'RODOVIARIA',
    'FERROVIARIA',
    'DUTOVIARIA',
    'POSTAL',
    'OUTRAS',
  ];

  // Função de busca de importadoras com debounce
  const buscarImportadoras = useCallback(
    debounce(async (query) => {
      if (!query || query.length < 2) {
        setImportadorasOptions([]);
        return;
      }
      
      setLoadingImportadoras(true);
      try {
        const response = await empresasAPI.autocompleteImportadoras(query);
        const options = response.data.map((empresa) => ({
          value: empresa.nome,
          label: `${empresa.nome} (${empresa.total_operacoes} operações)`,
          empresa: empresa,
        }));
        setImportadorasOptions(options);
      } catch (error) {
        console.error('Erro ao buscar importadoras:', error);
        setImportadorasOptions([]);
      } finally {
        setLoadingImportadoras(false);
      }
    }, 300),
    []
  );

  // Função de busca de exportadoras com debounce
  const buscarExportadoras = useCallback(
    debounce(async (query) => {
      if (!query || query.length < 2) {
        setExportadorasOptions([]);
        return;
      }
      
      setLoadingExportadoras(true);
      try {
        const response = await empresasAPI.autocompleteExportadoras(query);
        const options = response.data.map((empresa) => ({
          value: empresa.nome,
          label: `${empresa.nome} (${empresa.total_operacoes} operações)`,
          empresa: empresa,
        }));
        setExportadorasOptions(options);
      } catch (error) {
        console.error('Erro ao buscar exportadoras:', error);
        setExportadorasOptions([]);
      } finally {
        setLoadingExportadoras(false);
      }
    }, 300),
    []
  );

  const handleSearch = async (values, page = 1) => {
    setLoading(true);
    try {
      // Processar NCMs múltiplos
      let ncms = [];
      if (values.ncms && Array.isArray(values.ncms)) {
        ncms = values.ncms;
      } else if (values.ncm) {
        ncms = [values.ncm];
      }

      const filtros = {
        ...values,
        ncms: ncms.length > 0 ? ncms : undefined,
        ncm: undefined, // Remover campo antigo
        data_inicio: values.periodo?.[0]?.format('YYYY-MM-DD'),
        data_fim: values.periodo?.[1]?.format('YYYY-MM-DD'),
        periodo: undefined,
        empresa_importadora: values.empresa_importadora || undefined,
        empresa_exportadora: values.empresa_exportadora || undefined,
        page,
        page_size: pagination.pageSize,
      };

      const response = await buscaAPI.buscar(filtros);
      setResults(response.data.results);
      setPagination({
        ...pagination,
        current: page,
        total: response.data.total,
      });
    } catch (error) {
      message.error('Erro ao buscar dados');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (newPagination) => {
    const values = form.getFieldsValue();
    handleSearch(values, newPagination.current);
  };

  const handleExport = () => {
    message.info('Funcionalidade de exportação em desenvolvimento');
  };

  const columns = [
    {
      title: 'NCM',
      dataIndex: 'ncm',
      key: 'ncm',
      width: 100,
    },
    {
      title: 'Descrição',
      dataIndex: 'descricao_produto',
      key: 'descricao_produto',
      ellipsis: true,
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_operacao',
      key: 'tipo_operacao',
      width: 120,
      render: (tipo) => (
        <Tag color={tipo === 'Importação' ? 'green' : 'blue'}>
          {tipo}
        </Tag>
      ),
    },
    {
      title: 'País',
      dataIndex: 'pais_origem_destino',
      key: 'pais_origem_destino',
    },
    {
      title: 'UF',
      dataIndex: 'uf',
      key: 'uf',
      width: 60,
    },
    {
      title: 'Valor FOB (USD)',
      dataIndex: 'valor_fob',
      key: 'valor_fob',
      width: 150,
      render: (value) =>
        `$${value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
    },
    {
      title: 'Data',
      dataIndex: 'data_operacao',
      key: 'data_operacao',
      width: 120,
      render: (date) => dayjs(date).format('DD/MM/YYYY'),
    },
  ];

  return (
    <div>
      <Card title="Busca Avançada" bordered={false}>
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => handleSearch(values, 1)}
        >
          <Row gutter={16}>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="ncms" label="NCMs">
                <Select
                  mode="tags"
                  placeholder="Digite ou selecione NCMs (múltiplos)"
                  tokenSeparators={[',', ' ']}
                  filterOption={(input, option) =>
                    (option?.value ?? '').includes(input.replace(/[^\d]/g, ''))
                  }
                  style={{ width: '100%' }}
                >
                  {/* Opções podem ser adicionadas aqui se necessário */}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="tipo_operacao" label="Tipo de Operação">
                <Select placeholder="Selecione">
                  <Option value="Importação">Importação</Option>
                  <Option value="Exportação">Exportação</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="pais" label="País">
                <Input placeholder="Nome do país" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="uf" label="UF">
                <Select placeholder="Selecione UF" showSearch>
                  {ufs.map((uf) => (
                    <Option key={uf} value={uf}>
                      {uf}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="via_transporte" label="Via de Transporte">
                <Select placeholder="Selecione">
                  {viasTransporte.map((via) => (
                    <Option key={via} value={via}>
                      {via.replace('_', ' ')}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="periodo" label="Período">
                <RangePicker 
                  style={{ width: '100%' }}
                  defaultValue={[dayjs().subtract(2, 'year'), dayjs()]}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="empresa_importadora" label="Provável Importador">
                <AutoComplete
                  options={importadorasOptions}
                  onSearch={buscarImportadoras}
                  placeholder="Digite o nome da empresa importadora"
                  loading={loadingImportadoras}
                  filterOption={(inputValue, option) =>
                    option?.value?.toLowerCase().includes(inputValue.toLowerCase())
                  }
                  style={{ width: '100%' }}
                >
                  <Input 
                    prefix={<ImportOutlined />}
                    placeholder="Digite o nome da empresa importadora"
                  />
                </AutoComplete>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="empresa_exportadora" label="Provável Exportador">
                <AutoComplete
                  options={exportadorasOptions}
                  onSearch={buscarExportadoras}
                  placeholder="Digite o nome da empresa exportadora"
                  loading={loadingExportadoras}
                  filterOption={(inputValue, option) =>
                    option?.value?.toLowerCase().includes(inputValue.toLowerCase())
                  }
                  style={{ width: '100%' }}
                >
                  <Input 
                    prefix={<ExportOutlined />}
                    placeholder="Digite o nome da empresa exportadora"
                  />
                </AutoComplete>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="valor_fob_min" label="Valor FOB Mínimo (USD)">
                <Input type="number" placeholder="0.00" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="valor_fob_max" label="Valor FOB Máximo (USD)">
                <Input type="number" placeholder="0.00" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item>
            <Space>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                htmlType="submit"
                loading={loading}
              >
                Buscar
              </Button>
              <Button
                icon={<DownloadOutlined />}
                onClick={handleExport}
                disabled={!results}
              >
                Exportar
              </Button>
              <Button onClick={() => form.resetFields()}>Limpar</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {results && (
        <Card
          title={`Resultados (${pagination.total} registros)`}
          bordered={false}
          style={{ marginTop: 16 }}
        >
          <Table
            columns={columns}
            dataSource={results}
            loading={loading}
            pagination={pagination}
            onChange={handleTableChange}
            scroll={{ x: 1200 }}
            rowKey="id"
          />
        </Card>
      )}
    </div>
  );
};

export default BuscaAvancada;

