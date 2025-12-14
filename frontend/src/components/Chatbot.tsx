import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Loader2, Bot } from 'lucide-react';
import { sendChatMessage } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
    id: string;
    role: 'human' | 'ai';
    content: string;
}

const Chatbot: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        { id: 'aaa', role: 'ai', content: 'Hello! I am your NYC Transit assistant. Ask me about delays, routes, or station info.' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

    const handleSend = async () => {
        if (!inputValue.trim()) return;

        const userMsg: Message = { id: Date.now().toString(), role: 'human', content: inputValue };
        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setLoading(true);

        try {
            const response = await sendChatMessage(userMsg.content);
            const aiMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'ai',
                content: response.response || "Sorry, I couldn't process that."
            };
            setMessages(prev => [...prev, aiMsg]);
        } catch (error) {
            setMessages(prev => [...prev, { id: Date.now().toString(), role: 'ai', content: "Error connecting to server." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className="fixed bottom-24 right-4 md:right-8 w-[90vw] md:w-96 h-[600px] max-h-[80vh] flex flex-col z-[1000] overflow-hidden rounded-2xl shadow-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)]"
                    >
                        {/* Header */}
                        <div className="p-4 border-b border-[var(--border-subtle)] flex justify-between items-center bg-[var(--bg-card)]">
                            <div className="flex items-center gap-3">
                                <div className="bg-blue-600/20 p-2 rounded-lg">
                                    <Bot size={20} className="text-blue-500" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-[var(--text-main)] text-sm">Transit Assistant</h3>
                                    <div className="flex items-center gap-1.5 mt-0.5">
                                        <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                        <span className="text-xs text-[var(--text-scnd)]">Online</span>
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-2 hover:bg-[var(--bg-card-hover)] rounded-full text-[var(--text-scnd)] hover:text-[var(--text-main)] transition"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-[var(--bg-app)]">
                            {messages.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={`flex w-full ${msg.role === 'human' ? 'justify-end' : 'justify-start'}`}
                                >
                                    <div className={`flex flex-col max-w-[85%] ${msg.role === 'human' ? 'items-end' : 'items-start'}`}>
                                        <div
                                            className={`p-3.5 rounded-2xl text-sm leading-relaxed shadow-sm ${msg.role === 'human'
                                                    ? 'bg-blue-600 text-white rounded-br-none'
                                                    : 'bg-[var(--bg-card)] border border-[var(--border-subtle)] text-[var(--text-main)] rounded-bl-none'
                                                }`}
                                        >
                                            {msg.content}
                                        </div>
                                        <span className="text-[10px] text-[var(--text-muted)] mt-1 px-1">
                                            {msg.role === 'human' ? 'You' : 'Bot'}
                                        </span>
                                    </div>
                                </div>
                            ))}
                            {loading && (
                                <div className="flex justify-start w-full">
                                    <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] p-4 rounded-2xl rounded-bl-none flex items-center gap-2">
                                        <Loader2 className="animate-spin text-blue-500" size={16} />
                                        <span className="text-xs text-[var(--text-scnd)]">Thinking...</span>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input */}
                        <div className="p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-card)]">
                            <form
                                onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                                className="flex gap-2 items-center bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-full px-4 py-2 focus-within:border-blue-500 transition-colors"
                            >
                                <input
                                    type="text"
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    placeholder="Start typing..."
                                    className="flex-1 bg-transparent border-none focus:ring-0 text-sm text-[var(--text-main)] placeholder-[var(--text-muted)] h-8 outline-none"
                                />
                                <button
                                    type="submit"
                                    disabled={loading || !inputValue.trim()}
                                    className="p-2 bg-blue-600 rounded-full hover:bg-blue-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Send size={14} color="white" />
                                </button>
                            </form>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Toggle Button */}
            <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsOpen(!isOpen)}
                className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 rounded-full shadow-lg shadow-blue-900/40 flex items-center justify-center z-[1000] hover:bg-blue-500 transition-colors"
            >
                {isOpen ? <X size={24} color="white" /> : <MessageSquare size={24} color="white" />}
            </motion.button>
        </>
    );
};

export default Chatbot;
