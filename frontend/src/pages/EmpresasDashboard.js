import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert, Button, Card, Col, Empty, Row, Select, Space, Spin, Statistic, Table, Tag, Typography, message,
} from 'antd';
import { ApartmentOutlined, DownloadOutlined, SearchOutlined } from '@ant-design/icons';
import api from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const UFS = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG',
  'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
];

const CORES_SETOR = {
  'PRIMÁRIO': 'green', 'INDÚSTRIA': 'blue', 'DISTRIBUIDOR': 'geekblue',
  'VAREJO': 'orange', 'SERVIÇOS': 'purple',
};

export default function EmpresasDashboard() {
  const [arvore, setArvore] = useState({});
  const [loadingArvore, setLoadingArvore] = useState(true);

  const [setor, setSetor] = useState(undefined);
  const [segmento, setSegmento] = useState(undefined);
  const [ramo, setRamo] = useState(undefined);
  const [categoria, setCategoria] = useState(undefined);
  const [uf, setUf] = useState(undefined);

  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState(null);

  // Carregar árvore CNAE
  useEffect(() => {
    (async () => {
      setLoadingArvore(true);
      try {
        const res = await api.get('/api/empresa-intel/cnae-arvore');
        setArvore(res.data?.arvore || {});
      } catch {
        message.error('Erro ao carregar a árvore de segmentos CNAE.');
      } finally {
        setLoadingArvore(false);
      }
    })();
  }, []);

  // Opções em cascata derivadas da árvore
  const setores = useMemo(() => Object.keys(arvore).sort(), [arvore]);
  const segmentos = useMemo(
    () => (setor && arvore[setor] ? Object.keys(arvore[setor]).sort() : []),
    [arvore, setor]
  );
  const ramos = useMemo(
    () => (setor && segmento && arvore[setor]?.[segmento] ? Object.keys(arvore[setor][segmento]).sort() : []),
    [arvore, setor, segmento]
  );
  const categorias = useMemo(
    () => (setor && segmento && ramo && arvore[setor]?.[segmento]?.[ramo] ? arvore[setor][segmento][ramo] : []),
    [arvore, setor, segmento, ramo]
  );

  const onSetor = (v) => { setSetor(v); setSegmento(undefined); setRamo(undefined); setCategoria(undefined); };
  const onSegmento = (v) => { setSegmento(v); setRamo(undefined); setCategoria(undefined); };
  const onRamo = (v) => { setRamo(v); setCategoria(undefined); };

  const buscar = useCallback(async () => {
    if (!setor && !segmento) {
      message.warning('Selecione ao menos um Setor ou Segmento.');
      return;
    }
    setLoading(true);
    setResultado(null);
    try {
      const params = { limit: 300 };
      if (setor) params.setor = setor;
      if (segmento) params.segmento = segmento;
      if (ramo) params.ramo = ramo;
      if (categoria) params.categoria = categoria;
      if (uf) params.uf = uf;
      const res = await api.get('/api/empresa-intel/empresas-por-segmento', { params });
      if (res.data?.error) {
        message.error('Erro: ' + res.data.error);
      } else {
        setResultado(res.data);
      }
    } catch (e) {
      message.error('Erro ao buscar empresas do segmento.');
    } finally {
      setLoading(false);
    }
  }, [setor, segmento, ramo, categoria, uf]);

  const limpar = () => {
    setSetor(undefined); setSegmento(undefined); setRamo(undefined);
    setCategoria(undefined); setUf(undefined); setResultado(null);
  };

  const exportarCsv = () => {
    const emp = resultado?.empresas || [];
    if (!emp.length) return;
    const header = ['cnpj', 'razao_social', 'uf', 'cnae', 'setor', 'segmento', 'ramo', 'categoria', 'anos_ativos'];
    const linhas = emp.map((e) => header.map((h) => `"${String(e[h] ?? '').replace(/"/g, '""')}"`).join(','));
    const csv = [header.join(','), ...linhas].join('\n');
    const blob = new Blob([`﻿${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `empresas_${(segmento || setor || 'segmento').replace(/\W+/g, '_')}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const columns = [
    { title: 'CNPJ (raiz)', dataIndex: 'cnpj', key: 'cnpj', width: 110 },
    { title: 'Razão Social', dataIndex: 'razao_social', key: 'razao_social', ellipsis: true },
    { title: 'UF', dataIndex: 'uf', key: 'uf', width: 60, render: (v) => <Tag color="blue">{v}</Tag> },
    { title: 'CNAE', dataIndex: 'cnae', key: 'cnae', width: 90 },
    { title: 'Segmento', dataIndex: 'segmento', key: 'segmento', ellipsis: true, render: (v) => v ? <Tag color="geekblue">{v}</Tag> : '—' },
    { title: 'Ramo', dataIndex: 'ramo', key: 'ramo', ellipsis: true, render: (v) => v || '—' },
    {
      title: 'Anos Ativos', dataIndex: 'anos_ativos', key: 'anos_ativos', width: 100,
      sorter: (a, b) => a.anos_ativos - b.anos_ativos, defaultSortOrder: 'descend',
      render: (v) => <Tag color={v >= 10 ? 'green' : v >= 3 ? 'gold' : 'default'}>{v}</Tag>,
    },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Title level={2}>
        <ApartmentOutlined style={{ color: '#1890ff', marginRight: 8 }} />
        Empresas por Setor e Segmento
      </Title>
      <Text type="secondary">
        Explore empresas habilitadas em comércio exterior por hierarquia CNAE
        (Setor → Segmento → Ramo → Categoria). Filtre e veja o resumo por UF.
      </Text>

      <Card style={{ marginTop: 16, marginBottom: 16 }}>
        <Spin spinning={loadingArvore}>
          <Row gutter={[12, 12]} align="bottom">
            <Col xs={24} sm={12} md={8} lg={5}>
              <Text style={{ fontSize: 12 }}>Setor</Text>
              <Select allowClear showSearch placeholder="Todos" style={{ width: '100%' }} value={setor} onChange={onSetor}>
                {setores.map((s) => <Option key={s} value={s}>{s}</Option>)}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8} lg={5}>
              <Text style={{ fontSize: 12 }}>Segmento</Text>
              <Select allowClear showSearch placeholder="Todos" style={{ width: '100%' }} value={segmento} onChange={onSegmento} disabled={!setor}>
                {segmentos.map((s) => <Option key={s} value={s}>{s}</Option>)}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8} lg={5}>
              <Text style={{ fontSize: 12 }}>Ramo</Text>
              <Select allowClear showSearch placeholder="Todos" style={{ width: '100%' }} value={ramo} onChange={onRamo} disabled={!segmento}>
                {ramos.map((r) => <Option key={r} value={r}>{r}</Option>)}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8} lg={4}>
              <Text style={{ fontSize: 12 }}>Categoria</Text>
              <Select allowClear showSearch placeholder="Todas" style={{ width: '100%' }} value={categoria} onChange={setCategoria} disabled={!ramo}>
                {categorias.map((c) => <Option key={c} value={c}>{c}</Option>)}
              </Select>
            </Col>
            <Col xs={12} sm={8} md={6} lg={3}>
              <Text style={{ fontSize: 12 }}>UF</Text>
              <Select allowClear showSearch placeholder="Todas" style={{ width: '100%' }} value={uf} onChange={setUf}>
                {UFS.map((u) => <Option key={u} value={u}>{u}</Option>)}
              </Select>
            </Col>
            <Col xs={12} sm={16} md={6} lg={2}>
              <Space>
                <Button type="primary" icon={<SearchOutlined />} onClick={buscar} loading={loading}>Buscar</Button>
                <Button onClick={limpar}>Limpar</Button>
              </Space>
            </Col>
          </Row>
        </Spin>
      </Card>

      {loading && <div style={{ textAlign: 'center', padding: 48 }}><Spin size="large" /></div>}

      {resultado && !loading && (
        <>
          {/* Resumo */}
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={12} md={6}>
              <Card><Statistic title="Empresas no filtro" value={resultado.total || 0} /></Card>
            </Col>
            <Col xs={12} md={6}>
              <Card><Statistic title="Exibidas" value={resultado.exibidas || 0} suffix={`/ ${resultado.total || 0}`} /></Card>
            </Col>
            <Col xs={24} md={12}>
              <Card size="small" title="Distribuição por UF">
                {(resultado.resumo_uf || []).length === 0 ? <Text type="secondary">—</Text> : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {resultado.resumo_uf.map((u) => (
                      <Tag key={u.uf} color="blue">{u.uf}: {u.n}</Tag>
                    ))}
                  </div>
                )}
              </Card>
            </Col>
          </Row>

          {/* Contexto do filtro */}
          <div style={{ marginBottom: 12 }}>
            <Space wrap>
              {resultado.filtros?.setor && <Tag color={CORES_SETOR[resultado.filtros.setor] || 'default'}>Setor: {resultado.filtros.setor}</Tag>}
              {resultado.filtros?.segmento && <Tag color="geekblue">Segmento: {resultado.filtros.segmento}</Tag>}
              {resultado.filtros?.ramo && <Tag color="purple">Ramo: {resultado.filtros.ramo}</Tag>}
              {resultado.filtros?.categoria && <Tag color="magenta">Categoria: {resultado.filtros.categoria}</Tag>}
              {resultado.filtros?.uf && <Tag color="blue">UF: {resultado.filtros.uf}</Tag>}
            </Space>
          </div>

          {(resultado.empresas || []).length === 0 ? (
            <Empty description="Nenhuma empresa encontrada para este filtro." />
          ) : (
            <Card
              title={`Empresas (${resultado.exibidas} de ${resultado.total})`}
              size="small"
              extra={<Button size="small" icon={<DownloadOutlined />} onClick={exportarCsv}>CSV</Button>}
            >
              <Table
                rowKey="cnpj"
                columns={columns}
                dataSource={resultado.empresas}
                size="small"
                pagination={{ pageSize: 20, showSizeChanger: true }}
                scroll={{ x: 900 }}
              />
            </Card>
          )}
        </>
      )}

      {!resultado && !loading && (
        <Alert
          type="info" showIcon
          message="Selecione um setor/segmento e clique em Buscar"
          description="Ex.: Setor PRIMÁRIO → Segmento MINERAÇÃO retorna as mineradoras habilitadas em comércio exterior, com distribuição por estado."
        />
      )}
    </div>
  );
}
