import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Typography, DatePicker, Radio, Tabs } from 'antd';
import { MailOutlined, LockOutlined, UserOutlined, ShopOutlined, IdcardOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const Login = () => {
  const [loading, setLoading] = useState(false);
  const [registerLoading, setRegisterLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');
  const navigate = useNavigate();
  const [loginForm] = Form.useForm();
  const [registerForm] = Form.useForm();

  const onLoginFinish = async (values) => {
    setLoading(true);
    try {
      console.log('Tentando fazer login com:', values.email);
      
      // Truncar senha se necessário (bcrypt limite: 72 bytes)
      let senha = values.password;
      const senhaBytes = new TextEncoder().encode(senha).length;
      if (senhaBytes > 72) {
        // Truncar para 72 bytes
        const encoder = new TextEncoder();
        const decoder = new TextDecoder('utf-8', { fatal: false });
        const bytes = encoder.encode(senha);
        const bytesTruncados = bytes.slice(0, 72);
        senha = decoder.decode(bytesTruncados);
        console.warn(`⚠️ Senha truncada de ${senhaBytes} para 72 bytes no frontend`);
      }
      
      const formData = new FormData();
      formData.append('username', values.email); // OAuth2 usa 'username' mas é email
      formData.append('password', senha);

      console.log('Enviando requisição de login...');
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/login`,
        formData,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          timeout: 10000, // Timeout de 10 segundos
        }
      );

      console.log('Resposta do login:', response.data);

      if (response.data && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        console.log('Token salvo, redirecionando...');
        message.success('Login realizado com sucesso!');
        
        // Pequeno delay para garantir que a mensagem apareça
        setTimeout(() => {
          navigate('/dashboard');
        }, 500);
      } else {
        console.error('Resposta inválida:', response.data);
        message.error('Resposta inválida do servidor');
      }
    } catch (error) {
      console.error('Erro completo ao fazer login:', error);
      console.error('Resposta do erro:', error.response);
      
      if (error.response) {
        // Erro do servidor
        const detail = error.response.data?.detail || error.response.data?.message || 'Erro desconhecido';
        message.error(`Erro: ${detail}`);
        console.error('Detalhes do erro:', detail);
      } else if (error.request) {
        // Erro de conexão
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        message.error(`Não foi possível conectar ao servidor em ${apiUrl}. Verifique se o backend está rodando.`);
        console.error('Erro de conexão:', error.request);
        console.error('URL tentada:', apiUrl);
      } else {
        // Outro erro
        message.error(`Erro ao fazer login: ${error.message}`);
        console.error('Erro:', error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const onRegisterFinish = async (values) => {
    setRegisterLoading(true);
    try {
      console.log('Dados do formulário:', values);
      
      // Limpar CPF/CNPJ (remover formatação)
      let documentoLimpo = null;
      if (values.documento) {
        documentoLimpo = values.documento.replace(/[^\d]/g, ''); // Remove tudo exceto números
      }
      
      // Truncar senha se necessário (bcrypt limite: 72 bytes)
      let senha = values.password;
      const senhaBytes = new TextEncoder().encode(senha).length;
      if (senhaBytes > 72) {
        // Truncar para 72 bytes
        const encoder = new TextEncoder();
        const decoder = new TextDecoder('utf-8', { fatal: false });
        const bytes = encoder.encode(senha);
        const bytesTruncados = bytes.slice(0, 72);
        senha = decoder.decode(bytesTruncados);
        console.warn(`⚠️ Senha truncada de ${senhaBytes} para 72 bytes no frontend (cadastro)`);
      }
      
      const payload = {
        email: values.email?.trim(),
        password: senha,
        nome_completo: values.nome_completo?.trim(),
        data_nascimento: values.data_nascimento ? values.data_nascimento.format('YYYY-MM-DD') : null,
        nome_empresa: values.nome_empresa?.trim() || null,
        cpf: values.tipo_documento === 'cpf' ? documentoLimpo : null,
        cnpj: values.tipo_documento === 'cnpj' ? documentoLimpo : null,
      };

      console.log('Payload enviado:', payload);

      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/register`,
        payload,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 10000, // Timeout de 10 segundos
        }
      );

      console.log('Resposta do servidor:', response.data);
      
      if (response.status === 200) {
        const mensagem = response.data?.message || 'Cadastro realizado com sucesso! Aguarde aprovação por email.';
        message.success(mensagem);
        console.log('✅ Cadastro finalizado com sucesso!');
        
        // Limpar formulário
        registerForm.resetFields();
        
        // Mudar para aba de login após 2 segundos
        setTimeout(() => {
          setActiveTab('login');
          message.info('Agora você pode fazer login após aprovação do cadastro.');
        }, 2000);
      } else {
        console.warning('Resposta inesperada:', response.status, response.data);
        message.warning('Cadastro realizado, mas resposta inesperada do servidor.');
      }
    } catch (error) {
      console.error('Erro completo ao cadastrar:', error);
      console.error('Resposta do erro:', error.response);
      
      if (error.response) {
        // Erro do servidor
        const detail = error.response.data?.detail || error.response.data?.message || 'Erro desconhecido';
        message.error(`Erro: ${detail}`);
        console.error('Detalhes do erro:', detail);
      } else if (error.request) {
        // Erro de conexão
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        message.error(`Não foi possível conectar ao servidor em ${apiUrl}. Verifique se o backend está rodando.`);
        console.error('Erro de conexão:', error.request);
        console.error('URL tentada:', apiUrl);
        console.error('Dica: Execute REINICIAR_BACKEND.bat para iniciar o backend');
      } else {
        // Outro erro
        message.error(`Erro ao realizar cadastro: ${error.message}`);
        console.error('Erro:', error.message);
      }
    } finally {
      setRegisterLoading(false);
    }
  };

  // Validação de senha (deve conter letras e números)
  // IMPORTANTE: Bcrypt tem limite físico de 72 bytes que não pode ser alterado
  const validatePassword = (_, value) => {
    if (!value) {
      return Promise.reject(new Error('Por favor, insira sua senha!'));
    }
    if (value.length < 6) {
      return Promise.reject(new Error('Senha deve ter no mínimo 6 caracteres'));
    }
    // Limitar a 60 caracteres para dar margem de segurança
    // (caracteres especiais podem ocupar mais bytes)
    if (value.length > 60) {
      return Promise.reject(new Error('Senha deve ter no máximo 60 caracteres'));
    }
    // Verificar tamanho em bytes também (aproximado)
    const bytes = new TextEncoder().encode(value).length;
    if (bytes > 72) {
      return Promise.reject(new Error(`Senha muito longa (${bytes} bytes). Máximo: 72 bytes. Use uma senha mais curta.`));
    }
    const hasLetter = /[a-zA-Z]/.test(value);
    const hasNumber = /[0-9]/.test(value);
    if (!hasLetter) {
      return Promise.reject(new Error('Senha deve conter pelo menos uma letra'));
    }
    if (!hasNumber) {
      return Promise.reject(new Error('Senha deve conter pelo menos um número'));
    }
    return Promise.resolve();
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #722ed1 0%, #9254de 100%)',
      padding: '20px'
    }}>
      <Card
        style={{
          width: '100%',
          maxWidth: '500px',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <Title level={2} style={{ color: '#722ed1', marginBottom: '8px' }}>
            Comex Analyzer
          </Title>
          <Text type="secondary">Sistema de Análise de Comércio Exterior</Text>
        </div>

        <Tabs activeKey={activeTab} onChange={setActiveTab} centered>
          <TabPane tab="Login" key="login">
            <Form
              form={loginForm}
              name="login"
              onFinish={onLoginFinish}
              autoComplete="off"
              layout="vertical"
              size="large"
            >
              <Form.Item
                name="email"
                label="Email"
                rules={[
                  { required: true, message: 'Por favor, insira seu email!' },
                  { type: 'email', message: 'Email inválido!' }
                ]}
              >
                <Input
                  prefix={<MailOutlined />}
                  placeholder="seu@email.com"
                  autoComplete="email"
                />
              </Form.Item>

              <Form.Item
                name="password"
                label="Senha"
                rules={[{ required: true, message: 'Por favor, insira sua senha!' }]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="Senha"
                  autoComplete="current-password"
                  maxLength={60}
                />
              </Form.Item>

              <Form.Item>
                <div style={{ textAlign: 'right', marginBottom: '16px' }}>
                  <Button
                    type="link"
                    onClick={() => setActiveTab('redefinir')}
                    style={{ padding: 0 }}
                  >
                    Esqueci minha senha
                  </Button>
                </div>
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  block
                  style={{
                    background: '#722ed1',
                    border: 'none',
                    height: '40px',
                    fontSize: '16px'
                  }}
                >
                  Entrar
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab="Cadastro" key="register">
            <Form
              form={registerForm}
              name="register"
              onFinish={onRegisterFinish}
              autoComplete="off"
              layout="vertical"
              size="large"
            >
              <Form.Item
                name="nome_completo"
                label="Nome Completo"
                rules={[{ required: true, message: 'Por favor, insira seu nome completo!' }]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="Seu nome completo"
                />
              </Form.Item>

              <Form.Item
                name="email"
                label="Email"
                rules={[
                  { required: true, message: 'Por favor, insira seu email!' },
                  { type: 'email', message: 'Email inválido!' }
                ]}
              >
                <Input
                  prefix={<MailOutlined />}
                  placeholder="seu@email.com"
                  autoComplete="email"
                />
              </Form.Item>

              <Form.Item
                name="password"
                label="Senha"
                rules={[{ validator: validatePassword }]}
                hasFeedback
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="Senha (6-60 caracteres, letras e números)"
                  autoComplete="new-password"
                  maxLength={60}
                />
              </Form.Item>

              <Form.Item
                name="confirm_password"
                label="Confirmar Senha"
                dependencies={['password']}
                rules={[
                  { required: true, message: 'Por favor, confirme sua senha!' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('password') === value) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error('As senhas não coincidem!'));
                    },
                  }),
                ]}
                hasFeedback
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="Confirme sua senha"
                  autoComplete="new-password"
                />
              </Form.Item>

              <Form.Item
                name="data_nascimento"
                label="Data de Nascimento"
              >
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Selecione sua data de nascimento"
                />
              </Form.Item>

              <Form.Item
                name="nome_empresa"
                label="Nome da Empresa"
              >
                <Input
                  prefix={<ShopOutlined />}
                  placeholder="Nome da sua empresa (opcional)"
                />
              </Form.Item>

              <Form.Item
                name="tipo_documento"
                label="Tipo de Documento"
                initialValue="cpf"
              >
                <Radio.Group>
                  <Radio value="cpf">CPF</Radio>
                  <Radio value="cnpj">CNPJ</Radio>
                </Radio.Group>
              </Form.Item>

              <Form.Item
                noStyle
                shouldUpdate={(prevValues, currentValues) =>
                  prevValues.tipo_documento !== currentValues.tipo_documento
                }
              >
                {({ getFieldValue }) => {
                  const tipoDoc = getFieldValue('tipo_documento');
                  return (
                    <Form.Item
                      name="documento"
                      label={tipoDoc === 'cpf' ? 'CPF' : 'CNPJ'}
                      rules={[
                        {
                          required: true,
                          message: `Por favor, insira seu ${tipoDoc === 'cpf' ? 'CPF' : 'CNPJ'}!`,
                        },
                        {
                          validator: (_, value) => {
                            if (!value) {
                              return Promise.resolve();
                            }
                            // Remover formatação para validar
                            const apenasNumeros = value.replace(/[^\d]/g, '');
                            if (tipoDoc === 'cpf' && apenasNumeros.length !== 11) {
                              return Promise.reject(new Error('CPF deve ter 11 dígitos'));
                            }
                            if (tipoDoc === 'cnpj' && apenasNumeros.length !== 14) {
                              return Promise.reject(new Error('CNPJ deve ter 14 dígitos'));
                            }
                            return Promise.resolve();
                          },
                        },
                      ]}
                    >
                      <Input
                        prefix={<IdcardOutlined />}
                        placeholder={tipoDoc === 'cpf' ? '000.000.000-00 ou apenas números' : '00.000.000/0000-00 ou apenas números'}
                        maxLength={tipoDoc === 'cpf' ? 14 : 18}
                      />
                    </Form.Item>
                  );
                }}
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={registerLoading}
                  block
                  style={{
                    background: '#722ed1',
                    border: 'none',
                    height: '40px',
                    fontSize: '16px'
                  }}
                >
                  Cadastrar
                </Button>
              </Form.Item>

              <div style={{ textAlign: 'center', marginTop: '16px' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  Após o cadastro, você receberá um email para aprovação.
                </Text>
              </div>
            </Form>
          </TabPane>

          <TabPane tab="Redefinir Senha" key="redefinir">
            <Form
              name="redefinir"
              onFinish={async (values) => {
                try {
                  const response = await axios.post(
                    `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/solicitar-redefinicao-senha`,
                    { email: values.email }
                  );
                  message.success('Se o email existir, você receberá instruções para redefinir a senha');
                  setActiveTab('login');
                } catch (error) {
                  message.error('Erro ao solicitar redefinição de senha');
                }
              }}
              layout="vertical"
              size="large"
            >
              <Form.Item
                name="email"
                label="Email"
                rules={[
                  { required: true, message: 'Por favor, insira seu email!' },
                  { type: 'email', message: 'Email inválido!' }
                ]}
              >
                <Input
                  prefix={<MailOutlined />}
                  placeholder="seu@email.com"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  block
                  style={{
                    background: '#722ed1',
                    border: 'none',
                    height: '40px',
                    fontSize: '16px'
                  }}
                >
                  Enviar Link de Redefinição
                </Button>
              </Form.Item>

              <div style={{ textAlign: 'center', marginTop: '16px' }}>
                <Button type="link" onClick={() => setActiveTab('login')}>
                  Voltar para Login
                </Button>
              </div>
            </Form>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Login;
