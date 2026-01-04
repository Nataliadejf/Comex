import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  DatePicker,
  Select,
  AutoComplete,
  Button,
  Row,
  Col,
  Table,
  Space,
  Tag,
  message,
} from 'antd';
import { SearchOutlined, DownloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { buscaAPI, empresasAPI } from '../services/api';

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
  const [empresasOptions, setEmpresasOptions] = useState([]);

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

  const handleSearch = async (values, page = 1) => {
    setLoading(true);
    try {
      const filtros = {
        ...values,
        data_inicio: values.periodo?.[0]?.format('YYYY-MM-DD'),
        data_fim: values.periodo?.[1]?.format('YYYY-MM-DD'),
        periodo: undefined,
        page,
        page_size: pagination.pageSize,
      };

      const response = await buscaAPI.buscar(filtros);
      
      if (response.data && response.data.results !== undefined) {
        setResults(response.data.results || []);
        setPagination({
          ...pagination,
          current: page,
          total: response.data.total || 0,
        });
        
        if (response.data.total === 0) {
          message.info('Nenhum resultado encontrado. O banco de dados pode estar vazio.');
        }
      } else {
        setResults([]);
        setPagination({
          ...pagination,
          current: page,
          total: 0,
        });
        message.warning('Resposta inválida do servidor');
      }
    } catch (error) {
      console.error('Erro detalhado:', error);
      console.error('URL da API:', process.env.REACT_APP_API_URL || 'http://localhost:8000');
      if (error.response) {
        message.error(`Erro ${error.response.status}: ${error.response.data?.detail || 'Erro ao buscar dados'}`);
      } else if (error.request) {
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        message.error(`Não foi possível conectar ao backend em ${apiUrl}. Verifique se está rodando.`);
        console.error('Erro de conexão. Verifique:', {
          url: apiUrl,
          erro: error.message,
          request: error.request
        });
      } else {
        message.error('Erro ao buscar dados: ' + (error.message || 'Erro desconhecido'));
      }
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
      width: 180,
      render: (tipo, record) => {
        const isImp = record.is_importacao === 'S';
        const isExp = record.is_exportacao === 'S';
        return (
          <Space direction="vertical" size="small">
            <Tag color={isImp ? 'green' : 'default'}>
              {isImp ? '✓ Importação' : '✗ Não Importação'}
            </Tag>
            <Tag color={isExp ? 'blue' : 'default'}>
              {isExp ? '✓ Exportação' : '✗ Não Exportação'}
            </Tag>
          </Space>
        );
      },
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
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="ncm" label="NCM">
                <Input placeholder="Código NCM (8 dígitos)" maxLength={8} />
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
              <Form.Item name="empresa" label="Empresa">
                <AutoComplete
                  placeholder="Digite o nome da empresa..."
                  onSearch={async (value) => {
                    if (value && value.length >= 2) {
                      try {
                        console.log('Buscando empresas para:', value);
                        const response = await empresasAPI.autocomplete(value, 10);
                        console.log('Resposta autocomplete:', response.data);
                        const empresas = response.data?.empresas || [];
                        setEmpresasOptions(empresas.map(emp => ({ value: emp, label: emp })));
                      } catch (error) {
                        console.error('Erro ao buscar empresas:', error);
                        console.error('Detalhes do erro:', error.response?.data || error.message);
                        setEmpresasOptions([]);
                      }
                    } else {
                      setEmpresasOptions([]);
                    }
                  }}
                  options={empresasOptions}
                  allowClear
                  filterOption={false}
                  notFoundContent={empresasOptions.length === 0 ? 'Digite pelo menos 2 caracteres' : null}
                />
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
                <RangePicker style={{ width: '100%' }} />
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

