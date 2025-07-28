import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      logout();
    }
    setLoading(false);
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { access_token, user: userData } = response.data;

    localStorage.setItem('token', access_token);
    setToken(access_token);
    setUser(userData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

    return userData;
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);

      // Simplified - all registrations work immediately
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(user);

      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      return { requires_verification: false };
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Currency formatter for Mexican Pesos
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN'
  }).format(amount);
};

// Components
const LandingPage = () => {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-600 to-red-600">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="flex flex-col lg:flex-row items-center justify-between">
          <div className="lg:w-1/2 text-white mb-12 lg:mb-0">
            <h1 className="text-5xl lg:text-6xl font-bold mb-6">
              🇲🇽 RapidMandados
            </h1>
            <p className="text-xl lg:text-2xl mb-8 text-green-100">
              Tu aplicación de confianza para entregas rápidas y mandados en México
            </p>
            <p className="text-lg mb-8 text-green-200">
              Conectamos clientes con repartidores para entregas seguras y rápidas en toda la República Mexicana
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={() => setShowRegister(true)}
                className="bg-white text-green-600 px-8 py-3 rounded-full font-semibold text-lg hover:bg-green-50 transition-all"
              >
                Registrarse Gratis
              </button>
              <button
                onClick={() => setShowLogin(true)}
                className="border-2 border-white text-white px-8 py-3 rounded-full font-semibold text-lg hover:bg-white hover:text-green-600 transition-all"
              >
                Iniciar Sesión
              </button>
            </div>
            <div className="mt-4 text-green-200 text-sm">
              💰 Desde $50 MXN - Comisión del 15% + $15 MXN por entrega
            </div>
          </div>

          <div className="lg:w-1/2 flex justify-center">
            <div className="relative">
              <img
                src="https://images.unsplash.com/photo-1647221597996-54f3d0f73809?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwxfHxkZWxpdmVyeSUyMGFwcHxlbnwwfHx8Ymx1ZXwxNzUzNTAzODQyfDA&ixlib=rb-4.1.0&q=85"
                alt="Delivery México"
                className="w-80 h-80 object-cover rounded-full shadow-2xl"
              />
              <div className="absolute -bottom-4 -right-4 bg-yellow-400 text-yellow-900 px-4 py-2 rounded-full font-bold shadow-lg">
                🇲🇽 ¡Órale!
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-white py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center text-gray-800 mb-12">
            ¿Por qué elegir RapidMandados en México?
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📱</span>
              </div>
              <h3 className="text-xl font-semibold mb-3 text-gray-800">Fácil de usar</h3>
              <p className="text-gray-600">
                Interfaz intuitiva para hacer pedidos en segundos en toda la República
              </p>
            </div>

            <div className="text-center p-6">
              <div className="bg-red-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🛵</span>
              </div>
              <h3 className="text-xl font-semibold mb-3 text-gray-800">Repartidores verificados</h3>
              <p className="text-gray-600">
                Todos nuestros repartidores están verificados y capacitados en México
              </p>
            </div>

            <div className="text-center p-6">
              <div className="bg-yellow-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-semibold mb-3 text-gray-800">Entregas rápidas</h3>
              <p className="text-gray-600">
                Seguimiento en tiempo real de tus pedidos por toda la ciudad
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Login Modal */}
      {showLogin && (
        <LoginModal onClose={() => setShowLogin(false)} />
      )}

      {/* Register Modal */}
      {showRegister && (
        <RegisterModal onClose={() => setShowRegister(false)} />
      )}
    </div>
  );
};

const LoginModal = ({ onClose }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(email, password);
      onClose();
    } catch (err) {
      setError('Credenciales inválidas');
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 w-full max-w-md">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Iniciar Sesión</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>

        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>
        </form>

        <div className="mt-4 text-center text-sm text-gray-600">
          <p>👑 Propietario: leonardo.luna@rapidmandados.com</p>
          <p className="text-xs mt-1">🇲🇽 RapidMandados México</p>
        </div>
      </div>
    </div>
  );
};

const RegisterModal = ({ onClose }) => {
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    user_type: 'client',
    address: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await register(formData);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al registrarse');
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 w-full max-w-md max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Registrarse - México 🇲🇽</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>

        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Teléfono
            </label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="+52 55 1234 5678"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dirección
            </label>
            <input
              type="text"
              name="address"
              value={formData.address}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de Usuario
            </label>
            <select
              name="user_type"
              value={formData.user_type}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            >
              <option value="client">Cliente</option>
              <option value="driver">Repartidor</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Registrando...' : 'Registrarse'}
          </button>
        </form>
      </div>
    </div>
  );
};

const AdminDashboard = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [payments, setPayments] = useState([]);
  const [payouts, setPayouts] = useState([]);
  const [cashCollections, setCashCollections] = useState([]);
  const [pendingDrivers, setPendingDrivers] = useState([]);
  const [commissionConfig, setCommissionConfig] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, usersRes, ordersRes, configRes, paymentsRes, payoutsRes, cashRes, pendingRes] = await Promise.all([
        axios.get(`${API}/admin/stats`),
        axios.get(`${API}/admin/users`),
        axios.get(`${API}/orders`),
        axios.get(`${API}/admin/commission-config`),
        axios.get(`${API}/payments/transactions`),
        axios.get(`${API}/admin/driver-payouts`),
        axios.get(`${API}/admin/cash-collections`),
        axios.get(`${API}/admin/pending-drivers`)
      ]);

      setStats(statsRes.data);
      setUsers(usersRes.data);
      setOrders(ordersRes.data);
      setCommissionConfig(configRes.data);
      setPayments(paymentsRes.data);
      setPayouts(payoutsRes.data);
      setCashCollections(cashRes.data);
      setPendingDrivers(pendingRes.data);
    } catch (error) {
      console.error('Error fetching admin data:', error);
    }
    setLoading(false);
  };

  const approveDriver = async (driverId, approved, comments = '') => {
    try {
      await axios.post(`${API}/admin/approve-driver/${driverId}`, {
        approved,
        comments
      });

      alert(approved ? 'Repartidor aprobado exitosamente' : 'Repartidor rechazado');
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Error approving driver:', error);
      alert('Error al procesar la aprobación');
    }
  };

  const processDriverPayout = async (payoutId) => {
    try {
      await axios.post(`${API}/admin/process-driver-payout/${payoutId}`);
      alert('Pago a repartidor procesado exitosamente');
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Error processing payout:', error);
      alert('Error al procesar pago a repartidor');
    }
  };

  const markCommissionPaid = async (collectionId) => {
    try {
      await axios.post(`${API}/admin/mark-commission-paid/${collectionId}`);
      alert('Comisión marcada como pagada');
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Error marking commission as paid:', error);
      alert('Error al marcar comisión como pagada');
    }
  };

  const updateCommissionConfig = async (newConfig) => {
    try {
      await axios.put(`${API}/admin/commission-config`, newConfig);
      setCommissionConfig(newConfig);
      alert('Configuración actualizada exitosamente');
    } catch (error) {
      alert('Error al actualizar configuración');
    }
  };

  const toggleUserStatus = async (userId) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/toggle-status`);
      fetchData(); // Refresh data
    } catch (error) {
      alert('Error al cambiar estado del usuario');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">Cargando panel de administrador...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-green-600">👑 Panel de Administrador - México 🇲🇽</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-700">¡Hola, {user.name}!</span>
            <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-semibold">
              Propietario MX
            </span>
            <button
              onClick={logout}
              className="text-red-600 hover:text-red-800"
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4">
          <div className="flex space-x-8">
            {[
              { key: 'overview', label: 'Resumen', icon: '📊' },
              { key: 'orders', label: 'Pedidos', icon: '📦' },
              { key: 'users', label: 'Usuarios', icon: '👥' },
              { key: 'pending-drivers', label: 'Repartidores Pendientes', icon: '⏳' },
              { key: 'payments', label: 'Pagos', icon: '💳' },
              { key: 'payouts', label: 'Pagos a Repartidores', icon: '💰' },
              { key: 'cash', label: 'Cobros en Efectivo', icon: '💵' },
              { key: 'config', label: 'Configuración', icon: '⚙️' }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-4 py-4 border-b-2 font-medium ${
                  activeTab === tab.key
                    ? 'border-green-600 text-green-600'
                    : 'border-transparent text-gray-600 hover:text-gray-800'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {activeTab === 'overview' && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Resumen de RapidMandados México 🇲🇽</h2>

            {/* Stats Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <div className="bg-green-100 p-3 rounded-full">
                    <span className="text-2xl">💰</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-600">Ingresos Totales MXN</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(stats?.total_revenue || 0)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <div className="bg-red-100 p-3 rounded-full">
                    <span className="text-2xl">🏆</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-600">Comisiones Ganadas MXN</p>
                    <p className="text-2xl font-bold text-red-600">
                      {formatCurrency(stats?.total_commission_earned || 0)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <div className="bg-blue-100 p-3 rounded-full">
                    <span className="text-2xl">📦</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-600">Total Pedidos</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {stats?.total_orders || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <div className="bg-yellow-100 p-3 rounded-full">
                    <span className="text-2xl">👥</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-600">Usuarios Activos MX</p>
                    <p className="text-2xl font-bold text-yellow-600">
                      {stats?.active_users || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Monthly Performance */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Rendimiento Mensual (MXN) 🇲🇽</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Ingresos del Mes:</span>
                    <span className="font-semibold text-green-600">
                      {formatCurrency(stats?.monthly_revenue || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Comisiones del Mes:</span>
                    <span className="font-semibold text-red-600">
                      {formatCurrency(stats?.monthly_commission || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Valor Promedio de Pedido:</span>
                    <span className="font-semibold text-blue-600">
                      {formatCurrency(stats?.average_order_value || 0)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Estado de Pedidos</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Pendientes:</span>
                    <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-sm font-medium">
                      {stats?.pending_orders || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Completados:</span>
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm font-medium">
                      {stats?.completed_orders || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Repartidores Activos:</span>
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm font-medium">
                      {stats?.active_drivers || 0}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'orders' && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Gestión de Pedidos - México 🇲🇽</h2>

            {orders.length === 0 ? (
              <div className="bg-white rounded-lg p-12 text-center">
                <div className="text-6xl mb-4">📦</div>
                <h3 className="text-xl font-semibold text-gray-700 mb-2">No hay pedidos</h3>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Cliente
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Pedido
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Repartidor
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Estado
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Valor (MXN)
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Comisión (MXN)
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {orders.map((order) => (
                        <tr key={order.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {order.client_name}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-sm text-gray-900">{order.title}</div>
                            <div className="text-sm text-gray-500 truncate max-w-xs">
                              {order.description}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {order.driver_name || 'Sin asignar'}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              order.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              order.status === 'accepted' ? 'bg-blue-100 text-blue-800' :
                              order.status === 'in_progress' ? 'bg-purple-100 text-purple-800' :
                              order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {order.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(order.financials?.total_amount || order.price)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-medium">
                            {formatCurrency(order.financials?.owner_earnings || 0)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'users' && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Gestión de Usuarios - México 🇲🇽</h2>

            <div className="bg-white rounded-lg shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Usuario
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tipo
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Pedidos
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ganancias (MXN)
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {user.name}
                            </div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            user.user_type === 'client' ? 'bg-blue-100 text-blue-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {user.user_type === 'client' ? 'Cliente' : 'Repartidor'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {user.total_orders || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(user.total_earnings || 0)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            user.is_active !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {user.is_active !== false ? 'Activo' : 'Inactivo'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => toggleUserStatus(user.id)}
                            className={`${
                              user.is_active !== false
                                ? 'text-red-600 hover:text-red-900'
                                : 'text-green-600 hover:text-green-900'
                            }`}
                          >
                            {user.is_active !== false ? 'Desactivar' : 'Activar'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'pending-drivers' && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Repartidores Pendientes de Aprobación 🇲🇽</h2>

            <div className="bg-white rounded-lg shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Repartidor
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Teléfono
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Verificación
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Documentos
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Registro
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {pendingDrivers.map((driver) => (
                      <tr key={driver.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{driver.name}</div>
                          <div className="text-sm text-gray-500">{driver.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {driver.phone}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col space-y-1">
                            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              driver.is_phone_verified ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              📱 {driver.is_phone_verified ? 'Teléfono ✓' : 'Teléfono ✗'}
                            </span>
                            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              driver.is_email_verified ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              📧 {driver.is_email_verified ? 'Email ✓' : 'Email ✗'}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col space-y-1">
                            {driver.documents.map((doc, index) => (
                              <span key={index} className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                doc.status === 'approved' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {doc.type === 'ine' ? '📄 INE' : '🚗 Licencia'} {doc.status === 'approved' ? '✓' : '📋'}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(driver.created_at).toLocaleDateString('es-MX')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => approveDriver(driver.id, true)}
                              className="text-green-600 hover:text-green-900 bg-green-100 px-3 py-1 rounded"
                            >
                              ✅ Aprobar
                            </button>
                            <button
                              onClick={() => approveDriver(driver.id, false, 'Documentos no válidos')}
                              className="text-red-600 hover:text-red-900 bg-red-100 px-3 py-1 rounded"
                            >
                              ❌ Rechazar
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {pendingDrivers.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-gray-500">No hay repartidores pendientes de aprobación</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'payments' && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Transacciones de Pago - México 🇲🇽</h2>

            <div className="bg-white rounded-lg shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ID de Transacción
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Pedido
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Usuario
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Monto
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Fecha
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {payments.map((payment) => (
                      <tr key={payment.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {payment.session_id ? payment.session_id.substring(0, 20) + '...' : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {payment.order_id ? payment.order_id.substring(0, 8) : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {payment.user_id ? payment.user_id.substring(0, 8) : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(payment.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            payment.payment_status === 'paid' ? 'bg-green-100 text-green-800' :
                            payment.payment_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {payment.payment_status === 'paid' ? 'Pagado' :
                             payment.payment_status === 'pending' ? 'Pendiente' :
                             payment.payment_status === 'cancelled' ? 'Cancelado' : 'Expirado'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(payment.created_at).toLocaleDateString('es-MX')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'payouts' && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Pagos a Repartidores - México 🇲🇽</h2>

            <div className="bg-white rounded-lg shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Repartidor
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Pedido
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Monto
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {payouts.map((payout) => (
                      <tr key={payout.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{payout.driver_name}</div>
                          <div className="text-sm text-gray-500">{payout.driver_email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {payout.order_title}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(payout.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            payout.transfer_status === 'completed' ? 'bg-green-100 text-green-800' :
                            payout.transfer_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {payout.transfer_status === 'completed' ? 'Completado' :
                             payout.transfer_status === 'pending' ? 'Pendiente' : 'Error'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          {payout.transfer_status === 'pending' && (
                            <button
                              onClick={() => processDriverPayout(payout.id)}
                              className="text-green-600 hover:text-green-900"
                            >
                              Procesar Pago
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'cash' && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Cobros en Efectivo - México 🇲🇽</h2>

            <div className="bg-white rounded-lg shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Repartidor
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Pedido
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cobrado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Comisión Debida
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {cashCollections.map((collection) => (
                      <tr key={collection.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{collection.driver_name}</div>
                          <div className="text-sm text-gray-500">{collection.driver_email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {collection.order_title}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(collection.amount_collected)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(collection.commission_owed)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            collection.payment_status === 'paid' ? 'bg-green-100 text-green-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {collection.payment_status === 'paid' ? 'Pagado' : 'Pendiente'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          {collection.payment_status === 'pending' && (
                            <button
                              onClick={() => markCommissionPaid(collection.id)}
                              className="text-green-600 hover:text-green-900"
                            >
                              Marcar como Pagado
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'config' && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Configuración de Comisiones - México 🇲🇽</h2>

            {commissionConfig ? (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <CommissionConfigForm
                  config={commissionConfig}
                  onUpdate={updateCommissionConfig}
                />
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="text-center py-8">
                  <div className="loading-spinner"></div>
                  <p className="text-gray-600 mt-2">Cargando configuración...</p>
                </div>
              </div>
            )}

            {/* Removed Stripe Integration Section */}
          </div>
        )}
      </div>
    </div>
  );
};

const CommissionConfigForm = ({ config, onUpdate }) => {
  const [formData, setFormData] = useState({
    commission_rate: config.commission_rate,
    service_fee: config.service_fee,
    premium_subscription_monthly: config.premium_subscription_monthly
  });

  const handleChange = (e) => {
    const value = e.target.name === 'commission_rate'
      ? parseFloat(e.target.value)
      : parseFloat(e.target.value);

    setFormData({
      ...formData,
      [e.target.name]: value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onUpdate(formData);
  };

  const calculatePreview = () => {
    const price = 300.00; // Example order of $300 MXN
    const serviceFee = formData.service_fee;
    const commissionRate = formData.commission_rate;
    const ivaAmount = serviceFee * 0.16; // 16% IVA on service fee

    return {
      subtotal: price,
      serviceFee: serviceFee,
      ivaAmount: ivaAmount,
      commission: price * commissionRate,
      total: price + serviceFee + ivaAmount,
      ownerEarnings: (price * commissionRate) + serviceFee,
      driverEarnings: price * (1 - commissionRate)
    };
  };

  const preview = calculatePreview();

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tasa de Comisión (%)
        </label>
        <input
          type="number"
          name="commission_rate"
          value={formData.commission_rate}
          onChange={handleChange}
          min="0"
          max="1"
          step="0.01"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
          required
        />
        <p className="text-sm text-gray-500 mt-1">
          Porcentaje que recibes por cada pedido (actual: {(formData.commission_rate * 100).toFixed(1)}%)
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tarifa de Servicio (MXN)
        </label>
        <input
          type="number"
          name="service_fee"
          value={formData.service_fee}
          onChange={handleChange}
          min="0"
          step="0.50"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
          required
        />
        <p className="text-sm text-gray-500 mt-1">
          Tarifa fija cobrada al cliente por pedido (actual: {formatCurrency(formData.service_fee)})
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Suscripción Premium Mensual (MXN)
        </label>
        <input
          type="number"
          name="premium_subscription_monthly"
          value={formData.premium_subscription_monthly}
          onChange={handleChange}
          min="0"
          step="10"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
          required
        />
        <p className="text-sm text-gray-500 mt-1">
          Precio mensual para repartidores premium (actual: {formatCurrency(formData.premium_subscription_monthly)})
        </p>
      </div>

      {/* Preview */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-800 mb-3">Vista previa - Pedido de {formatCurrency(300)}:</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span>Subtotal del pedido:</span>
            <span>{formatCurrency(preview.subtotal)}</span>
          </div>
          <div className="flex justify-between">
            <span>Tarifa de servicio:</span>
            <span>{formatCurrency(preview.serviceFee)}</span>
          </div>
          <div className="flex justify-between">
            <span>IVA (16% sobre tarifa):</span>
            <span>{formatCurrency(preview.ivaAmount)}</span>
          </div>
          <div className="flex justify-between">
            <span>Comisión ({(formData.commission_rate * 100).toFixed(1)}%):</span>
            <span className="text-green-600 font-medium">
              {formatCurrency(preview.commission)}
            </span>
          </div>
          <div className="flex justify-between border-t pt-2 font-medium">
            <span>Total cliente paga:</span>
            <span>{formatCurrency(preview.total)}</span>
          </div>
          <div className="flex justify-between text-green-600 font-medium">
            <span>Tus ganancias:</span>
            <span>{formatCurrency(preview.ownerEarnings)}</span>
          </div>
          <div className="flex justify-between text-blue-600">
            <span>Repartidor recibe:</span>
            <span>{formatCurrency(preview.driverEarnings)}</span>
          </div>
        </div>
      </div>

      <button
        type="submit"
        className="w-full bg-green-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-green-700 transition-colors"
      >
        Actualizar Configuración
      </button>
    </form>
  );
};

const ClientDashboard = () => {
  const { user, logout } = useAuth();
  const [orders, setOrders] = useState([]);
  const [showCreateOrder, setShowCreateOrder] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
    setLoading(false);
  };

  const handlePayment = async (order) => {
    // Only handle cash payment
    try {
      await axios.post(`${API}/payment/cash`, {
        order_id: order.id
      });

      alert('Pedido configurado para pago en efectivo. El repartidor cobrará al entregar.');
      fetchOrders(); // Refresh orders
    } catch (error) {
      console.error('Error processing payment:', error);
      alert('Error al procesar el pago. Por favor, intenta de nuevo.');
    }
  };

  const completeCashPayment = async (orderId) => {
    try {
      await axios.post(`${API}/payment/cash/complete/${orderId}`);
      alert('Pago en efectivo completado exitosamente');
      fetchOrders(); // Refresh orders
    } catch (error) {
      console.error('Error completing cash payment:', error);
      alert('Error al completar el pago en efectivo');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      accepted: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-purple-100 text-purple-800',
      delivered: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status) => {
    const texts = {
      pending: 'Pendiente',
      accepted: 'Aceptado',
      in_progress: 'En camino',
      delivered: 'Entregado',
      cancelled: 'Cancelado'
    };
    return texts[status] || status;
  };

  const getPaymentStatusText = (paymentStatus) => {
    const texts = {
      pending: 'Pendiente de pago',
      paid: 'Pagado',
      cancelled: 'Pago cancelado',
      expired: 'Pago expirado'
    };
    return texts[paymentStatus] || paymentStatus;
  };

  const getPaymentStatusColor = (paymentStatus) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      paid: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      expired: 'bg-gray-100 text-gray-800'
    };
    return colors[paymentStatus] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-green-600">🇲🇽 RapidMandados México</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-700">¡Hola, {user.name}!</span>
            <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm">
              Cliente MX
            </span>
            <button
              onClick={logout}
              className="text-red-600 hover:text-red-800"
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold text-gray-800">Mis Pedidos</h2>
          <button
            onClick={() => setShowCreateOrder(true)}
            className="bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 flex items-center gap-2"
          >
            <span>+</span> Crear Pedido
          </button>
        </div>

        {/* Orders Grid */}
        {orders.length === 0 ? (
          <div className="bg-white rounded-lg p-12 text-center">
            <div className="text-6xl mb-4">📦</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              No tienes pedidos aún
            </h3>
            <p className="text-gray-500 mb-6">
              Crea tu primer pedido para comenzar en México 🇲🇽
            </p>
            <button
              onClick={() => setShowCreateOrder(true)}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
            >
              Crear Pedido
            </button>
          </div>
        ) : (
          <div className="grid gap-6">
            {orders.map((order) => (
              <div key={order.id} className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-800">
                      {order.title}
                    </h3>
                    <p className="text-gray-600">{order.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="flex flex-col items-end gap-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
                        {getStatusText(order.status)}
                      </span>
                      {order.payment_status && (
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPaymentStatusColor(order.payment_status)}`}>
                          {getPaymentStatusText(order.payment_status)}
                        </span>
                      )}
                    </div>
                    <div className="text-xl font-bold text-green-600 mt-2">
                      {formatCurrency(order.financials?.total_amount || order.price)}
                    </div>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
                  <div>
                    <strong>Recoger en:</strong>
                    <div>{order.pickup_address}</div>
                  </div>
                  <div>
                    <strong>Entregar en:</strong>
                    <div>{order.delivery_address}</div>
                  </div>
                </div>

                {/* Financial Breakdown */}
                {order.financials && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex justify-between">
                        <span>Subtotal:</span>
                        <span>{formatCurrency(order.financials.subtotal)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Tarifa de servicio:</span>
                        <span>{formatCurrency(order.financials.service_fee)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>IVA (16%):</span>
                        <span>{formatCurrency(order.financials.iva_amount || 0)}</span>
                      </div>
                      <div className="flex justify-between col-span-2 border-t pt-2 font-semibold">
                        <span>Total MXN:</span>
                        <span>{formatCurrency(order.financials.total_amount)}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Payment Options (Only Cash) */}
                {order.status === 'pending' && order.payment_status !== 'paid' && (
                  <div className="mt-4 space-y-2">
                    <button
                      onClick={() => handlePayment(order)}
                      className="w-full py-3 px-4 rounded-lg font-semibold transition-colors bg-yellow-600 text-white hover:bg-yellow-700"
                    >
                      💵 Pagar en Efectivo - {formatCurrency(order.financials?.total_amount || order.price)}
                    </button>
                  </div>
                )}

                {order.driver_name && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <strong>Repartidor:</strong> {order.driver_name}
                  </div>
                )}

                <div className="mt-4 text-sm text-gray-500">
                  Creado el {new Date(order.created_at).toLocaleDateString('es-MX')}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create Order Modal */}
        {showCreateOrder && (
          <CreateOrderModal
            onClose={() => setShowCreateOrder(false)}
            onOrderCreated={() => {
              setShowCreateOrder(false);
              fetchOrders();
            }}
          />
        )}
      </div>
    </div>
  );
};

const CreateOrderModal = ({ onClose, onOrderCreated }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    pickup_address: '',
    delivery_address: '',
    price: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const calculatePreview = () => {
    const price = parseFloat(formData.price) || 0;
    const serviceFee = 15.00; // From APP_CONFIG
    const commissionRate = 0.15; // From APP_CONFIG
    const ivaAmount = serviceFee * 0.16; // 16% IVA on service fee

    return {
      subtotal: price,
      serviceFee: serviceFee,
      ivaAmount: ivaAmount,
      commission: price * commissionRate,
      total: price + serviceFee + ivaAmount
    };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const orderData = {
        ...formData,
        price: parseFloat(formData.price)
      };
      await axios.post(`${API}/orders`, orderData);
      onOrderCreated();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al crear el pedido');
    }
    setLoading(false);
  };

  const preview = calculatePreview();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 w-full max-w-md max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Crear Pedido - México 🇲🇽</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>

        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Título del pedido
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="ej. Comprar medicinas en farmacia del Ahorro"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripción
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Detalles específicos del pedido en México..."
              rows="3"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dirección de recogida (México)
            </label>
            <input
              type="text"
              name="pickup_address"
              value={formData.pickup_address}
              onChange={handleChange}
              placeholder="Colonia, Delegación/Municipio, Estado"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dirección de entrega (México)
            </label>
            <input
              type="text"
              name="delivery_address"
              value={formData.delivery_address}
              onChange={handleChange}
              placeholder="Colonia, Delegación/Municipio, Estado"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Valor del pedido (MXN)
            </label>
            <input
              type="number"
              name="price"
              value={formData.price}
              onChange={handleChange}
              placeholder="300.00"
              min="50"
              max="5000"
              step="10"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Mínimo $50 MXN - Máximo $5,000 MXN</p>
          </div>

          {/* Cost Preview */}
          {formData.price && parseFloat(formData.price) > 0 && (
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-800 mb-2">Resumen de costos (MXN) 🇲🇽:</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Valor del pedido:</span>
                  <span>{formatCurrency(preview.subtotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tarifa de servicio:</span>
                  <span>{formatCurrency(preview.serviceFee)}</span>
                </div>
                <div className="flex justify-between">
                  <span>IVA (16%):</span>
                  <span>{formatCurrency(preview.ivaAmount)}</span>
                </div>
                <div className="flex justify-between border-t pt-1 font-semibold">
                  <span>Total a pagar MXN:</span>
                  <span className="text-green-600">{formatCurrency(preview.total)}</span>
                </div>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Creando pedido...' : 'Crear Pedido'}
          </button>
        </form>
      </div>
    </div>
  );
};

const DriverVerificationSystem = () => {
  const { user } = useAuth();
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [emailVerificationSent, setEmailVerificationSent] = useState(false);
  const [emailCode, setEmailCode] = useState('');
  const [uploadingDocument, setUploadingDocument] = useState(false);

  useEffect(() => {
    fetchVerificationStatus();
    fetchDocuments();
  }, []);

  const fetchVerificationStatus = async () => {
    try {
      const response = await axios.get(`${API}/verification/status`);
      setVerificationStatus(response.data);
    } catch (error) {
      console.error('Error fetching verification status:', error);
    }
    setLoading(false);
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/verification/documents`);
      setDocuments(response.data.documents);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const sendEmailVerification = async () => {
    try {
      await axios.post(`${API}/verification/send-email`);
      setEmailVerificationSent(true);
      alert('Código de verificación enviado a tu correo electrónico');
    } catch (error) {
      console.error('Error sending email verification:', error);
      alert('Error al enviar código de verificación');
    }
  };

  const verifyEmail = async () => {
    try {
      await axios.post(`${API}/verification/verify-email`, {
        verification_code: emailCode
      });
      alert('Correo verificado exitosamente');
      setEmailCode('');
      setEmailVerificationSent(false);
      fetchVerificationStatus();
    } catch (error) {
      console.error('Error verifying email:', error);
      alert('Código de verificación inválido');
    }
  };

  const handleFileUpload = async (documentType, file) => {
    if (!file) return;

    setUploadingDocument(true);
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64Data = e.target.result.split(',')[1];

        await axios.post(`${API}/verification/upload-document`, {
          document_type: documentType,
          file_name: file.name,
          file_data: base64Data
        });

        alert('Documento subido y verificado exitosamente');
        fetchDocuments();
        fetchVerificationStatus();
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error uploading document:', error);
      alert('Error al subir documento');
    }
    setUploadingDocument(false);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return '✅';
      case 'rejected':
        return '❌';
      case 'pending':
        return '⏳';
      default:
        return '❓';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'approved':
        return 'Aprobado';
      case 'rejected':
        return 'Rechazado';
      case 'pending':
        return 'Pendiente';
      default:
        return 'Sin subir';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-6 text-gray-800">🔐 Verificación de Seguridad</h2>

        {/* Overall Status */}
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-blue-900">Estado General</h3>
              <p className="text-sm text-blue-700">
                {verificationStatus?.overall_verification_complete
                  ? '✅ Verificación completa - Puedes aceptar pedidos'
                  : '⏳ Verificación pendiente - Completa los pasos siguientes'
                }
              </p>
            </div>
            <div className="text-right">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                verificationStatus?.can_accept_orders
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {verificationStatus?.can_accept_orders ? 'Activo' : 'Inactivo'}
              </span>
            </div>
          </div>
        </div>

        {/* Email Verification */}
        <div className="mb-6 p-4 border rounded-lg">
          <h3 className="font-semibold mb-3 flex items-center">
            📧 Verificación de Correo Electrónico
            {verificationStatus?.email_verified && <span className="ml-2 text-green-600">✅</span>}
          </h3>

          {!verificationStatus?.email_verified ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-600">
                Verifica tu correo electrónico: {user?.email}
              </p>

              {!emailVerificationSent ? (
                <button
                  onClick={sendEmailVerification}
                  className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                >
                  Enviar Código de Verificación
                </button>
              ) : (
                <div className="space-y-2">
                  <input
                    type="text"
                    placeholder="Ingresa el código de 6 dígitos"
                    value={emailCode}
                    onChange={(e) => setEmailCode(e.target.value)}
                    className="w-full p-2 border rounded"
                    maxLength="6"
                  />
                  <button
                    onClick={verifyEmail}
                    disabled={emailCode.length !== 6}
                    className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:bg-gray-400"
                  >
                    Verificar Correo
                  </button>
                </div>
              )}
            </div>
          ) : (
            <p className="text-green-600">✅ Correo verificado exitosamente</p>
          )}
        </div>

        {/* Document Upload */}
        <div className="mb-6 p-4 border rounded-lg">
          <h3 className="font-semibold mb-3">📄 Documentos Requeridos</h3>

          <div className="space-y-4">
            {/* INE */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">
                  {getStatusIcon(verificationStatus?.documents_status?.ine)}
                </span>
                <div>
                  <p className="font-medium">Identificación Oficial (INE)</p>
                  <p className="text-sm text-gray-600">
                    Estado: {getStatusText(verificationStatus?.documents_status?.ine)}
                  </p>
                </div>
              </div>

              {verificationStatus?.documents_status?.ine !== 'approved' && (
                <label className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 cursor-pointer">
                  {uploadingDocument ? 'Subiendo...' : 'Subir INE'}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleFileUpload('ine', e.target.files[0])}
                    className="hidden"
                    disabled={uploadingDocument}
                  />
                </label>
              )}
            </div>

            {/* Driver's License */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">
                  {getStatusIcon(verificationStatus?.documents_status?.drivers_license)}
                </span>
                <div>
                  <p className="font-medium">Licencia de Conducir</p>
                  <p className="text-sm text-gray-600">
                    Estado: {getStatusText(verificationStatus?.documents_status?.drivers_license)}
                  </p>
                </div>
              </div>

              {verificationStatus?.documents_status?.drivers_license !== 'approved' && (
                <label className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 cursor-pointer">
                  {uploadingDocument ? 'Subiendo...' : 'Subir Licencia'}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleFileUpload('drivers_license', e.target.files[0])}
                    className="hidden"
                    disabled={uploadingDocument}
                  />
                </label>
              )}
            </div>
          </div>
        </div>

        {/* Pending Actions */}
        {verificationStatus?.pending_actions && verificationStatus.pending_actions.length > 0 && (
          <div className="mb-6 p-4 bg-yellow-50 rounded-lg">
            <h3 className="font-semibold mb-3 text-yellow-800">⚠️ Acciones Pendientes</h3>
            <ul className="space-y-1">
              {verificationStatus.pending_actions.map((action, index) => (
                <li key={index} className="text-sm text-yellow-700">
                  • {action}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Verification Complete */}
        {verificationStatus?.overall_verification_complete && (
          <div className="p-4 bg-green-50 rounded-lg">
            <h3 className="font-semibold text-green-800">🎉 ¡Verificación Completa!</h3>
            <p className="text-sm text-green-700">
              Tu cuenta ha sido verificada exitosamente. Ahora puedes aceptar pedidos.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

const DriverDashboard = () => {
  const { user, logout } = useAuth();
  const [availableOrders, setAvailableOrders] = useState([]);
  const [myOrders, setMyOrders] = useState([]);
  const [activeTab, setActiveTab] = useState('available');
  const [loading, setLoading] = useState(true);
  const [verificationStatus, setVerificationStatus] = useState(null);

  useEffect(() => {
    fetchVerificationStatus();
    fetchOrders();
  }, []);

  const fetchVerificationStatus = async () => {
    try {
      const response = await axios.get(`${API}/verification/status`);
      setVerificationStatus(response.data);
    } catch (error) {
      console.error('Error fetching verification status:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const [availableResponse, myOrdersResponse] = await Promise.all([
        axios.get(`${API}/orders`),
        axios.get(`${API}/orders/driver`)
      ]);
      setAvailableOrders(availableResponse.data);
      setMyOrders(myOrdersResponse.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
    setLoading(false);
  };

  const completeCashPayment = async (orderId) => {
    try {
      await axios.post(`${API}/payment/cash/complete/${orderId}`);
      alert('Pago en efectivo completado exitosamente');
      fetchOrders(); // Refresh orders
    } catch (error) {
      console.error('Error completing cash payment:', error);
      alert('Error al completar el pago en efectivo');
    }
  };

  const acceptOrder = async (orderId) => {
    try {
      await axios.put(`${API}/orders/${orderId}/accept`);
      fetchOrders();
    } catch (error) {
      console.error('Error accepting order:', error);
      if (error.response?.status === 403) {
        alert('Debes completar la verificación de seguridad para aceptar pedidos');
      } else {
        alert('Error al aceptar el pedido');
      }
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.put(`${API}/orders/${order_id}/status?status=${status}`);
      fetchOrders();
    } catch (error) {
      console.error('Error updating order status:', error);
      alert('Error al actualizar el estado del pedido');
    }
  };

  // Show verification screen if not fully verified
  if (verificationStatus && !verificationStatus.can_accept_orders) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <h1 className="text-2xl font-bold text-gray-900">🚚 RapidMandados - Repartidor</h1>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">Hola, {user?.name}</span>
                <button
                  onClick={logout}
                  className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                >
                  Cerrar Sesión
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <DriverVerificationSystem />
        </div>
      </div>
    );
  }

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      accepted: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-purple-100 text-purple-800',
      delivered: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status) => {
    const texts = {
      pending: 'Pendiente',
      accepted: 'Aceptado',
      in_progress: 'En camino',
      delivered: 'Entregado',
      cancelled: 'Cancelado'
    };
    return texts[status] || status;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-green-600">🇲🇽 RapidMandados México</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-700">¡Hola, {user.name}!</span>
            <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm">
              Repartidor MX
            </span>
            <div className="text-sm text-gray-600">
              Ganancias: {formatCurrency(user.total_earnings || 0)}
            </div>
            <button
              onClick={logout}
              className="text-red-600 hover:text-red-800"
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4">
          <div className="flex">
            <button
              onClick={() => setActiveTab('available')}
              className={`px-6 py-3 font-medium ${
                activeTab === 'available'
                  ? 'border-b-2 border-green-600 text-green-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Pedidos Disponibles ({availableOrders.length})
            </button>
            <button
              onClick={() => setActiveTab('my-orders')}
              className={`px-6 py-3 font-medium ${
                activeTab === 'my-orders'
                  ? 'border-b-2 border-green-600 text-green-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Mis Pedidos ({myOrders.length})
            </button>
            <button
              onClick={() => setActiveTab('verification')}
              className={`px-6 py-3 font-medium ${
                activeTab === 'verification'
                  ? 'border-b-2 border-green-600 text-green-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              🔐 Verificación
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-6">
        {activeTab === 'available' && (
          <div>
            <h2 className="text-xl font-bold mb-4">Pedidos Disponibles</h2>
            {availableOrders.length === 0 ? (
              <p className="text-gray-600">No hay pedidos disponibles.</p>
            ) : (
              <div className="space-y-4">
                {availableOrders.map((order) => (
                  <div key={order.id} className="bg-white p-4 rounded-lg shadow-sm border">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-lg">{order.title}</h3>
                      <span className={`px-2 py-1 rounded-full text-sm ${getStatusColor(order.status)}`}>
                        {getStatusText(order.status)}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-2">{order.description}</p>
                    <div className="text-sm text-gray-500 mb-2">
                      <p>📍 Recoger: {order.pickup_address}</p>
                      <p>📍 Entregar: {order.delivery_address}</p>
                      <p>💰 Precio: {formatCurrency(order.price)}</p>
                      <p>👤 Cliente: {order.client_name}</p>
                    </div>
                    <button
                      onClick={() => acceptOrder(order.id)}
                      className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                    >
                      Aceptar Pedido
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'my-orders' && (
          <div>
            <h2 className="text-xl font-bold mb-4">Mis Pedidos</h2>
            {myOrders.length === 0 ? (
              <p className="text-gray-600">No tienes pedidos asignados.</p>
            ) : (
              <div className="space-y-4">
                {myOrders.map((order) => (
                  <div key={order.id} className="bg-white p-4 rounded-lg shadow-sm border">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-lg">{order.title}</h3>
                      <span className={`px-2 py-1 rounded-full text-sm ${getStatusColor(order.status)}`}>
                        {getStatusText(order.status)}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-2">{order.description}</p>
                    <div className="text-sm text-gray-500 mb-2">
                      <p>📍 Recoger: {order.pickup_address}</p>
                      <p>📍 Entregar: {order.delivery_address}</p>
                      <p>💰 Precio: {formatCurrency(order.price)}</p>
                      <p>👤 Cliente: {order.client_name}</p>
                    </div>

                    {/* Order Actions */}
                    <div className="flex gap-2 mt-4">
                      {order.status === 'accepted' && (
                        <button
                          onClick={() => updateOrderStatus(order.id, 'in_progress')}
                          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                        >
                          Marcar En Camino
                        </button>
                      )}
                      {order.status === 'in_progress' && (
                        <button
                          onClick={() => updateOrderStatus(order.id, 'delivered')}
                          className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                        >
                          Marcar Entregado
                        </button>
                      )}
                      {order.status === 'delivered' && order.payment_method === 'cash' && order.payment_status === 'pending' && (
                        <button
                          onClick={() => completeCashPayment(order.id)}
                          className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600"
                        >
                          Completar Pago en Efectivo
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'verification' && (
          <DriverVerificationSystem />
        )}
      </div>
    </div>
  );
};

function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">Cargando RapidMandados México...</div>
      </div>
    );
  }

  if (!user) {
    return <LandingPage />;
  }

  if (user.user_type === 'admin') {
    return <AdminDashboard />;
  }

  return user.user_type === 'client' ? <ClientDashboard /> : <DriverDashboard />;
}

function AppWithProvider() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWithProvider;